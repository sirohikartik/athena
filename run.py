from processes import search_query
from agent import agent
from rank_bm25 import BM25Okapi
from utils import model
import asyncio
import json
import os
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown

console = Console()

import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

HISTORY_DIR = "History"
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")
history = []


def load_history():
    global history
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            history = []


def save_history():
    os.makedirs(HISTORY_DIR, exist_ok=True)
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except:
        pass


def analyze_query(user_query: str, model_name: str = model.DEFAULT_MODEL) -> dict:
    """
    Analyzes the query to determine the type of result expected.
    """
    prompt = (
        f"Analyze the following user query:\n"
        f"Query: {user_query}\n\n"
        f"Return a JSON object with:\n"
        f"- type: 'structured' if the user wants a list of entities, people, products, or specific attributes; 'general' for a factual or conceptual answer.\n"
        f"- focus: the core subject of the query.\n"
        f"- requirements: a list of specific details the user explicitly asked for (e.g., ['email', 'price', 'date']).\n"
        f"Return ONLY the JSON object."
    )
    try:
        response = model.ask(prompt, model_name)
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            return json.loads(response[start_idx:end_idx])
    except Exception as e:
        console.print(f"[yellow]Query analysis failed: {e}[/yellow]")
    return {"type": "general", "focus": user_query, "requirements": []}


def generate_diversified_queries(user_query: str, analysis: dict, model_name: str = model.DEFAULT_MODEL) -> list[str]:
    """
    Generates diverse search queries based on whether the intent is structured or general.
    """
    q_type = analysis.get("type", "general")
    focus = analysis.get("focus", user_query)
    reqs = analysis.get("requirements", [])

    if q_type == "structured":
        prompt = (
            f"The user wants a structured list of entities related to '{focus}'. "
            f"They specifically need: {', '.join(reqs)}.\n"
            f"Generate 5 highly targeted search queries to find these details. "
            f"Mix general terms with specific attribute-seeking terms (e.g., ' la email', ' la portfolio', ' la price').\n"
            f"Return ONLY JSON: {{\"queries\": [\"q1\", \"q2\", ...]}}"
        )
    else:
        prompt = (
            f"The user wants a general answer about '{focus}'.\n"
            f"Generate 5 diverse search queries to cover this topic from multiple angles "
            f"(e.g., definition, current status, pros/cons, expert opinions).\n"
            f"Return ONLY JSON: {{\"queries\": [\"q1\", \"q2\", ...]}}"
        )
    try:
        response = model.ask(prompt, model_name)
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            data = json.loads(response[start_idx:end_idx])
            return data.get('queries', [user_query])
    except Exception as e:
        console.print(f"[yellow]Query generation failed: {e}[/yellow]")
    return [user_query]


def reason_about_search(user_query: str, current_context: str, iteration: int, analysis: dict, model_name: str = model.DEFAULT_MODEL) -> tuple[bool, list[str]]:
    """
    General purpose reasoning to decide if we need more information to satisfy the user's request.
    """
    prompt = (
        f"You are an information retrieval expert. Determine if the current context is sufficient to answer the user's request.\n\n"
        f"User Request: {user_query}\n"
        f"Expected Type: {analysis.get('type')} (Focus: {analysis.get('focus')})\n"
        f"Context gathered so far:\n{current_context[:2000] if current_context else 'Nothing yet.'}\n\n"
        f"Instruction:\n"
        f"1. If the answer is fully and accurately supported by the context, respond with 'DONE'.\n"
        f"2. If information is missing or contradictory, identify the gap and provide 2-3 search queries to fill it.\n"
        f"Return JSON if more info is needed: {{\"queries\": [\"q1\", \"q2\"]}}\n"
        f"Iteration: {iteration}/4\n"
        f"Response:"
    )
    try:
        response = model.ask(prompt, model_name).strip()
        if response.upper().startswith("DONE") or (response.count('\n') == 0 and "DONE" in response.upper()):
            return True, []
        
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            data = json.loads(response[start_idx:end_idx])
            queries = data.get('queries', [])
            if queries:
                return False, queries
    except Exception as e:
        console.print(f"[yellow]Reasoning failed: {e}[/yellow]")
    
    return (iteration >= 4), []


def tokenize(text):
    return text.lower().split()


def build_bm25_index(texts):
    tokenized_corpus = [tokenize(t) for t in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, tokenized_corpus, texts


def retrieve_bm25(query, bm25, tokenized_corpus, texts, k=3):
    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [texts[i] for i in top_indices]


def chunk_text(text, chunk_size=300):
    if not isinstance(text, str) or not text.strip():
        return []
    words = text.split()
    return [
        " ".join(words[i:i+chunk_size])
        for i in range(0, len(words), chunk_size)
    ]


async def main():
    global history

    user_query = input("\nAsk Athena: ").strip()
    if not user_query:
        return

    history.append({
        "timestamp": str(datetime.now()),
        "query": user_query
    })

    # Step 0: Analyze query intent (General vs Structured)
    console.print("[cyan]Analyzing query...[/cyan]")
    analysis = await asyncio.to_thread(analyze_query, user_query)
    console.print(f"[dim]Intent: {analysis['type']} | Focus: {analysis['focus']}[/dim]")

    # Step 1: Initial set of diverse queries
    current_queries = await asyncio.to_thread(generate_diversified_queries, user_query, analysis)
    
    all_chunks = []
    all_urls = []
    current_context = ""

    for iteration in range(1, 5):
        console.print(f"[cyan]Reasoning Loop Iteration {iteration}/4...[/cyan]")

        if iteration > 1:
            is_done, new_queries = await asyncio.to_thread(
                reason_about_search, user_query, current_context, iteration, analysis
            )
            if is_done:
                console.print("[green]Sufficient information gathered.[/green]")
                break
            current_queries = new_queries

        console.print(f"[dim]Searching for: {current_queries}[/dim]")
        console.print("[cyan]Searching...[/cyan]")

        tasks = [search_query.find(q) for q in current_queries]
        results = await asyncio.gather(*tasks)

        for context, urls in results:
            if context:
                for doc in context:
                    all_chunks.extend(chunk_text(doc))
                all_urls.extend(urls)

        if not all_chunks:
            console.print("[yellow]No content found in this pass...[/yellow]")
            if iteration == 1:
                # Fallback to raw query if the agent's first queries failed
                current_queries = [user_query]
            else:
                continue

        # Update BM25 index and retrieve for the reasoning loop
        bm25, tokenized_corpus, texts = await asyncio.to_thread(build_bm25_index, all_chunks)
        relevant = await asyncio.to_thread(retrieve_bm25, user_query, bm25, tokenized_corpus, texts, 10)
        current_context = "\n\n".join(relevant)

    if not all_chunks:
        console.print("[red]No usable content extracted after multiple attempts[/red]")
        return

    # Final Retrieval
    bm25, tokenized_corpus, texts = await asyncio.to_thread(build_bm25_index, all_chunks)
    relevant = await asyncio.to_thread(retrieve_bm25, user_query, bm25, tokenized_corpus, texts, 10)
    final_context = "\n\n".join(relevant)

    # Tailor the agent prompt based on the intent
    if analysis['type'] == 'structured':
        reqs = ", ".join(analysis['requirements']) if analysis['requirements'] else "all available details"
        agent_prompt = (
            f"The user is looking for a structured list of results related to '{analysis['focus']}'.\n"
            f"Please provide the results and ensure you include these details for each: {reqs}.\n"
            f"If a detail is missing from the context, mark it as 'Not found'. Do not guess.\n\n"
            f"Context:\n{final_context}\n\n"
            f"Question: {user_query}"
        )
    else:
        agent_prompt = (
            f"Answer the following question based on the provided context. "
            f"Be precise, objective, and well-structured.\n\n"
            f"Context:\n{final_context}\n\n"
            f"Question: {user_query}"
        )

    console.print("\n[bold green]Athena:[/bold green]")
    response = await asyncio.to_thread(agent, agent_prompt, model.DEFAULT_MODEL)
    console.print(Markdown(response))

    console.print("\n[bold yellow]Sources:[/bold yellow]")
    seen = set()
    for i, url in enumerate(all_urls, 1):
        if url not in seen:
            console.print(f"{i}. {url}")
            seen.add(url)
        if len(seen) >= 5:
            break


if __name__ == "__main__":
    load_history()
    try:
        while True:
            asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold]Saving history...[/bold]")
        save_history()
        console.print("Goodbye 👋")

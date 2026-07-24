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


def generate_search_queries(user_query: str, model_name: str = "gpt-oss:20b-cloud") -> list[str]:
    prompt = (
        f"You are an expert search query generator. Given the user's question, "
        f"break it down into 3-5 diverse and effective search queries to retrieve the most comprehensive information. "
        f"Return the result strictly as a JSON object with a key 'queries' containing a list of strings.\n\n"
        f"Question: {user_query}\n\n"
        f"JSON Response:"
    )
    try:
        response = model.ask(prompt, model_name)
        # Simple JSON extraction from response
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            data = json.loads(response[start_idx:end_idx])
            return data.get('queries', [user_query])
    except Exception as e:
        console.print(f"[yellow]Query generation failed: {e}. Using original query.[/yellow]")
    
    return [user_query]


def reason_about_search(user_query: str, current_context: str, iteration: int, model_name: str = "gpt-oss:20b-cloud") -> tuple[bool, list[str]]:
    prompt = (
        f"You are a research coordinator. Your goal is to determine if the provided context is sufficient to answer the user's question accurately.\n\n"
        f"Question: {user_query}\n\n"
        f"Context found so far:\n{current_context if current_context else 'No information gathered yet.'}\n\n"
        f"Instruction:\n"
        f"1. If the context is sufficient to provide a complete and accurate answer, respond with exactly one word: 'DONE'.\n"
        f"2. If more information is needed, identify the missing pieces and generate 2-4 targeted search queries to fill those gaps. "
        f"Return the result strictly as a JSON object with a key 'queries' containing a list of strings.\n\n"
        f"Current iteration: {iteration}/4\n\n"
        f"Response:"
    )
    try:
        response = model.ask(prompt, model_name)
        if "DONE" in response.upper():
            return True, []
        
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            data = json.loads(response[start_idx:end_idx])
            return False, data.get('queries', [])
    except Exception as e:
        console.print(f"[yellow]Reasoning failed: {e}. Proceeding to finish.[/yellow]")
    
    return True, []


def tokenize(text):
    return text.lower().split()


def build_bm25_index(texts):
    tokenized_corpus = [tokenize(t) for t in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, tokenized_corpus, texts


def retrieve_bm25(query, bm25, tokenized_corpus, texts, k=3):
    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)
    # get top k indices
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

    console.print("[cyan]Analyzing query and generating search terms...[/cyan]")
    
    # Generate multiple search queries
    search_queries = await asyncio.to_thread(generate_search_queries, user_query)
    console.print(f"[dim]Queries: {', '.join(search_queries)}[/dim]")

    console.print("[cyan]Searching...[/cyan]")

    # Perform searches in parallel
    tasks = [search_query.find(q) for q in search_queries]
    results = await asyncio.gather(*tasks)

    all_chunks = []
    all_urls = []
    
    for context, urls in results:
        if context:
            for doc in context:
                all_chunks.extend(chunk_text(doc))
            all_urls.extend(urls)

    if not all_chunks:
        console.print("[red]No usable content extracted[/red]")
        return

    # Build BM25 index
    bm25, tokenized_corpus, texts = await asyncio.to_thread(build_bm25_index, all_chunks)

    # Retrieve most relevant chunks using the ORIGINAL user query
    relevant = await asyncio.to_thread(retrieve_bm25, user_query, bm25, tokenized_corpus, texts, 5)

    final_context = "\n\n".join(relevant)
    console.print("\n[bold green]Athena:[/bold green]")

    response = await asyncio.to_thread(
        agent,
        final_context + "\n\nQuestion: " + user_query,
        "gpt-oss:20b-cloud"
    )


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

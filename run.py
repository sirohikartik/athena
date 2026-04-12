from processes import search_query
from agent import agent
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
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

print("Initializing sentencepiece...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")


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


def build_faiss_index(texts):
    embeddings = embed_model.encode(texts)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))
    return index, texts


def chunk_text(text, chunk_size=300):
    if not isinstance(text, str) or not text.strip():
        return []

    words = text.split()
    return [
        " ".join(words[i:i+chunk_size])
        for i in range(0, len(words), chunk_size)
    ]


def retrieve(query, index, texts, k=3):
    query_embedding = embed_model.encode([query])
    distances, indices = index.search(np.array(query_embedding), k)
    return [texts[i] for i in indices[0]]


async def main():
    global history

    query = input("\nAsk Athena: ").strip()
    if not query:
        return


    history.append({
        "timestamp": str(datetime.now()),
        "query": query
    })

    console.print("[cyan]Searching...[/cyan]")


    context, urls = await search_query.find(query)

    if not context:
        console.print("[red]No results found[/red]")
        return


    all_chunks = []
    for doc in context:
        all_chunks.extend(chunk_text(doc))

    if not all_chunks:
        console.print("[red]No usable content extracted[/red]")
        return


    index, texts = await asyncio.to_thread(build_faiss_index, all_chunks)


    relevant = await asyncio.to_thread(retrieve, query, index, texts, 3)

    final_context = "\n\n".join(relevant)
    console.print("\n[bold green]Athena:[/bold green]")

    response = await asyncio.to_thread(
        agent,
        final_context + "\n\nQuestion: " + query,
        "gemma3:1b"
    )


    console.print(Markdown(response))


    console.print("\n[bold yellow]Sources:[/bold yellow]")
    seen = set()
    for i, url in enumerate(urls, 1):
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

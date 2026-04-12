from processes import search_query
from utils import model
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import time

embed_model = SentenceTransformer("all-MiniLM-L6-v2")


def build_faiss_index(texts):
    embeddings = embed_model.encode(texts)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))

    return index, texts


def chunk_text(text, chunk_size=300):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))

    return chunks


def retrieve(query, index, texts, k=3):
    query_embedding = embed_model.encode([query])
    distances, indices = index.search(np.array(query_embedding), k)
    return [texts[i] for i in indices[0]]


# 🔹 TOTAL START

query = input(":")
total_start = time.time()

# 🔹 SEARCH
t1 = time.time()
context = search_query.find(query)
t2 = time.time()

# 🔹 CHUNKING
t3 = time.time()
all_chunks = []
for doc in context:
    all_chunks.extend(chunk_text(doc))
t4 = time.time()

# 🔹 FAISS BUILD
t5 = time.time()
index, texts = build_faiss_index(all_chunks)
t6 = time.time()

# 🔹 RETRIEVAL
t7 = time.time()
relevant = retrieve(query, index, texts, k=3)
t8 = time.time()

# 🔹 MODEL
t9 = time.time()
final_context = "\n\n".join(relevant)
response = model.ask(final_context + "\n\nQuestion: " + query, "gemma3:1b")
t10 = time.time()

# 🔹 TOTAL END
total_end = time.time()

# OUTPUT
print(response)

print("\n--- Latency Breakdown ---")
print(f"Search latency:       {t2 - t1:.4f}s")
print(f"Chunking latency:     {t4 - t3:.4f}s")
print(f"FAISS build latency:  {t6 - t5:.4f}s")
print(f"Retrieval latency:    {t8 - t7:.4f}s")
print(f"Model latency:        {t10 - t9:.4f}s")
print(f"Total latency:        {total_end - total_start:.4f}s")

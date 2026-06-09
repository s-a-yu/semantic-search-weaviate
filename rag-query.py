import sys
import requests

import weaviate

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

client = weaviate.Client("http://localhost:8080")


def retrieve(query, limit=4):
    result = (
        client.query
        .get("Document", ["author", "book", "chunkText", "chunkIndex"])
        .with_near_text({"concepts": [query]})
        .with_limit(limit)
        .do()
    )
    return result["data"]["Get"]["Document"]


def build_prompt(query, docs):
    context = "\n\n---\n\n".join(
        f"[{d['book']} by {d['author']}, chunk {d['chunkIndex']}]\n{d['chunkText']}"
        for d in docs
    )
    return (
        "Use the following excerpts to answer the question. "
        "If the answer isn't in the excerpts, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n"
        "Answer:"
    )


def generate(prompt):
    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["response"]


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Query: ")

    print(f"\nRetrieving chunks for: '{query}'...")
    docs = retrieve(query)

    if not docs:
        print("No relevant chunks found.")
        sys.exit(1)

    print(f"Found {len(docs)} relevant chunks:")
    for d in docs:
        print(f"  - {d['book']} by {d['author']} (chunk {d['chunkIndex']})")

    prompt = build_prompt(query, docs)

    print("\nGenerating answer...\n")
    answer = generate(prompt)
    print(answer)

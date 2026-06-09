from weaviate import Client
import os

client = Client(url="http://localhost:8080/")

try:
    client.schema.delete_class("Document")
except Exception as e:
    print(f"Warning: {e}")

class_obj = {
    "class": "Document",
    "vectorizer": "text2vec-transformers",
    "properties": [
        {
            "name": "author",
            "dataType": ["text"],
            "moduleConfig": {"text2vec-transformers": {"skip": True}}
        },
        {
            "name": "book",
            "dataType": ["text"],
            "moduleConfig": {"text2vec-transformers": {"skip": True}}
        },
        {
            "name": "chunkText",
            "dataType": ["text"]
        },
        {
            "name": "chunkIndex",
            "dataType": ["int"],
            "moduleConfig": {"text2vec-transformers": {"skip": True}}
        },
    ]
}
client.schema.create_class(class_obj)


def chunk_text(text, chunk_size=1500, overlap=150):
    separators = ["\n\n", "\n", ". ", " "]

    def _split(text, seps):
        if len(text) <= chunk_size:
            return [text.strip()] if text.strip() else []

        for i, sep in enumerate(seps):
            if sep not in text:
                continue

            parts = text.split(sep)
            chunks = []
            current = ""

            for part in parts:
                trial = (current + sep + part) if current else part
                if len(trial) <= chunk_size:
                    current = trial
                else:
                    if current.strip():
                        chunks.append(current.strip())
                    if len(part) > chunk_size:
                        chunks.extend(_split(part, seps[i + 1:] or []))
                        current = ""
                    else:
                        current = part

            if current.strip():
                chunks.append(current.strip())

            return chunks

        # No separator found — force split
        return [text[i:i + chunk_size].strip() for i in range(0, len(text), chunk_size - overlap)]

    raw_chunks = _split(text, separators)

    # Prepend tail of previous chunk for overlap
    result = []
    for i, chunk in enumerate(raw_chunks):
        if i > 0 and overlap > 0:
            tail = raw_chunks[i - 1][-overlap:].strip()
            chunk = tail + " " + chunk
        result.append(chunk)

    return result


data_dir = os.path.join(os.path.dirname(__file__), "data")

if not os.path.exists(data_dir):
    print("No 'data/' directory found. Create it and add .txt files named 'Author - Book.txt'")
    exit(1)

txt_files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]

if not txt_files:
    print("No .txt files found in data/. Add files named 'Author - Book.txt'")
    exit(1)

with client.batch as batch:
    batch.batch_size = 50
    for filename in txt_files:
        stem = os.path.splitext(filename)[0]
        if " - " in stem:
            author, book = stem.split(" - ", 1)
        else:
            author, book = "Unknown", stem

        author = author.strip()
        book = book.strip()

        with open(os.path.join(data_dir, filename), "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        print(f"\n'{book}' by {author}: {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            client.batch.add_data_object(
                {
                    "author": author,
                    "book": book,
                    "chunkText": chunk,
                    "chunkIndex": i,
                },
                "Document",
            )
            print(f"  chunk {i}: {len(chunk)} chars")

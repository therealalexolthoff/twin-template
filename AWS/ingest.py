import os
import chromadb
from dotenv import load_dotenv
from chunker import chunk_text
from doc_loader import prep_docs
from embed import run_embeddings

load_dotenv()

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "person_knowledge")
EMBED_BATCH_SIZE = 100 


def build_and_upload():
    all_chunks = []
    for doc in prep_docs():
        all_chunks.extend(chunk_text(doc["text"], doc["source"]))

    if not all_chunks:
        print("WARNING: knowledge documents are empty — no context to retrieve.")
        return

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    existing = collection.get()["ids"]
    if existing:
        collection.delete(existing)

    texts = [c["text"] for c in all_chunks]
    embeddings = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i:i + EMBED_BATCH_SIZE]
        embeddings.extend(run_embeddings(batch, "RETRIEVAL_DOCUMENT"))
        print(f"Embedded {min(i + EMBED_BATCH_SIZE, len(texts))}/{len(texts)} chunks")

    collection.add(
        ids=[c["id"] for c in all_chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in all_chunks],
        metadatas=[
            {"source": c["source"], "chunk_id": c["id"], "length": c["length"]}
            for c in all_chunks
        ],
    )
    print(f"Indexed {len(all_chunks)} chunks into '{COLLECTION_NAME}'.")

    index_bucket = os.environ.get("INDEX_BUCKET")
    if not index_bucket:
        print("INDEX_BUCKET not set — index left at ./chroma_db only (local dev mode).")
        return

    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(index_bucket)
    for root, _, files in os.walk(CHROMA_PATH):
        for fname in files:
            local_path = os.path.join(root, fname)
            rel_path = os.path.relpath(local_path, CHROMA_PATH)
            bucket.blob(f"chroma_db/{rel_path}").upload_from_filename(local_path)
    print(f"Uploaded index to gs://{index_bucket}/chroma_db/")


if __name__ == "__main__":
    build_and_upload()
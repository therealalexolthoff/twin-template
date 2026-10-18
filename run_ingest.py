import os
import shutil
import tempfile
import chromadb
from dotenv import load_dotenv
from ingest.chunker import chunk_text
from ingest.doc_loader import prep_docs
from shared.embed import run_embeddings

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "person_knowledge")


def build_and_upload():
    all_chunks = []
    for doc in prep_docs():
        all_chunks.extend(chunk_text(doc["text"], doc["source"]))

    if not all_chunks:
        print("WARNING: knowledge documents are empty — no context to retrieve.")
        return

    # Embed everything before touching the existing index, so a failed run
    # leaves the old index in place instead of an empty one.
    texts = [c["text"] for c in all_chunks]
    embeddings = run_embeddings(texts, "RETRIEVAL_DOCUMENT")

    # Build the new index in a fresh folder, then swap it in for the old one.
    # Chroma never deletes a dropped collection's files, so reusing the old
    # folder would leave stale data behind (and upload it). A fresh folder also
    # means the collection is always created with the current settings.
    build_path = tempfile.mkdtemp(prefix="chroma_build_", dir=BASE_DIR)
    try:
        chroma_client = chromadb.PersistentClient(path=build_path)
        collection = chroma_client.create_collection(
            name=COLLECTION_NAME,
            configuration={"hnsw": {"space": "cosine"}},
        )
        collection.add(
            ids=[c["id"] for c in all_chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {"source": c["source"], "chunk_id": c["id"], "length": c["length"]}
                for c in all_chunks
            ],
        )
    except Exception:
        shutil.rmtree(build_path, ignore_errors=True)
        raise

    shutil.rmtree(CHROMA_PATH, ignore_errors=True)
    os.replace(build_path, CHROMA_PATH)
    print(f"Indexed {len(all_chunks)} chunks into '{COLLECTION_NAME}'.")

    index_bucket = os.environ.get("INDEX_BUCKET")
    if not index_bucket:
        print("INDEX_BUCKET not set — index left at ./chroma_db only (local dev mode).")
        return

    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(index_bucket)
    uploaded = set()
    for root, _, files in os.walk(CHROMA_PATH):
        for fname in files:
            local_path = os.path.join(root, fname)
            rel_path = os.path.relpath(local_path, CHROMA_PATH)
            blob_name = f"chroma_db/{rel_path}"
            bucket.blob(blob_name).upload_from_filename(local_path)
            uploaded.add(blob_name)

    # Remove files left over from previous runs only after the new index is
    # fully uploaded, so the bucket never holds a half-empty index.
    for blob in bucket.list_blobs(prefix="chroma_db/"):
        if blob.name not in uploaded:
            blob.delete()
    print(f"Uploaded index to gs://{index_bucket}/chroma_db/")


if __name__ == "__main__":
    build_and_upload()

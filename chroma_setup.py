import os
import chromadb


CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "person_knowledge")
 
_collection = None

def _download_index_if_needed():
    if os.path.exists(CHROMA_PATH):
        return
    index_bucket = os.environ.get("INDEX_BUCKET")
    if not index_bucket:
        # No bucket configured and nothing local — get_or_create_collection
        # below will just start an empty collection.
        return
    from google.cloud import storage
 
    client = storage.Client()
    bucket = client.bucket(index_bucket)
    blobs = list(bucket.list_blobs(prefix="chroma_db/"))
    for blob in blobs:
        rel_path = blob.name[len("chroma_db/"):]
        if not rel_path:
            continue
        dest = os.path.join(CHROMA_PATH, rel_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        blob.download_to_filename(dest)
    print(f"Downloaded index from gs://{index_bucket}/chroma_db/")

def get_collection():
    """Returns the Chroma collection, downloading the pre-built index from
    GCS on first call if it isn't present locally. Never re-embeds or
    rebuilds anything — that's ingest.py's job, run separately."""
    global _collection
    if _collection is None:
        _download_index_if_needed()
        chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection

COLLECTION = build_collection("alex")

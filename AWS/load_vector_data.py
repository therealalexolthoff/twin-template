import os
import chromadb

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "person_knowledge")

_collection = None


def get_collection():
    global _collection
    if _collection is None:
        chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection
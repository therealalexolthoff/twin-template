import os
from pathlib import Path

def prep_docs():

    docs_bucket = os.environ.get("DOCS_BUCKET")

    if docs_bucket:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(docs_bucket)
        documents = []
        for blob in bucket.list_blobs():
            if not blob.name.endswith(".txt"):
                continue
            print(f"Reading: gs://{docs_bucket}/{blob.name}")
            documents.append({"text": blob.download_as_text(), "source": blob.name})
        return documents

    documents = []
    base_dir = Path(__file__).resolve().parent
    folder_path = base_dir / ".." / "rag_data"
    # Only .txt files, matching the bucket branch above — this also skips
    # stray files like macOS's .DS_Store.
    for file_path in sorted(folder_path.glob("*.txt")):
        if file_path.is_file():
            print(f"Reading: {file_path.name}")
            with file_path.open("r", encoding="utf-8") as file:
                documents.append({"text": file.read(), "source": file_path.name})
    return documents


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
    folder_path = Path("./rag_data")
    for file_path in folder_path.iterdir():
        if file_path.is_file():
            print(f"Reading: {file_path.name}")
            with file_path.open("r") as file:
                documents.append({"text": file.read(), "source": file_path.name})
    return documents


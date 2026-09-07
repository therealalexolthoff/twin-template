import os
from pathlib import Path

DOCS_DIR = os.environ.get("DOCS_DIR", "./rag_data")


def prep_docs():
    folder_path = Path(DOCS_DIR)

    if not folder_path.is_dir():
        raise FileNotFoundError(
            f"Docs folder '{folder_path}' does not exist. "
            f"Create it and add your .txt source documents, or set DOCS_DIR."
        )

    documents = []
    for file_path in sorted(folder_path.iterdir()):
        if file_path.is_file() and file_path.suffix == ".txt":
            print(f"Reading: {file_path.name}")
            with file_path.open("r") as file:
                documents.append({"text": file.read(), "source": file_path.name})
    return documents
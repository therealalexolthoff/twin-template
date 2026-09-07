# Function for embedding using Cohere Embed v3 on Bedrock
import json
import os
from instantiate_bedrock import bedrock_client

COHERE_MODEL_ID = os.environ.get("COHERE_EMBED_MODEL_ID", "cohere.embed-english-v3")

# Cohere Embed on Bedrock caps each invoke_model call at 96 texts, so a  larger batch (e.g. ingest.py's EMBED_BATCH_SIZE) gets split into sub-batches here rather than sent in one request.
COHERE_MAX_TEXTS_PER_CALL = 96

# The rest of this project passes task_type using the naming used elsewhere ("RETRIEVAL_QUERY" / "RETRIEVAL_DOCUMENT"). Cohere calls this input_type and uses its own values, so it's translated here.
_TASK_TYPE_TO_INPUT_TYPE = {
    "RETRIEVAL_QUERY": "search_query",
    "RETRIEVAL_DOCUMENT": "search_document",
}


def run_embeddings(input, task_type="RETRIEVAL_DOCUMENT"):
    """
    Embed a single string or a list of strings with Cohere Embed v3.

    Returns a single embedding vector if `input` is a string, or a list
    of embedding vectors (one per item, in order) if `input` is a list.
    """
    is_batch = not isinstance(input, str)
    texts = list(input) if is_batch else [input]
    input_type = _TASK_TYPE_TO_INPUT_TYPE.get(task_type, "search_document")

    embeddings = []
    for i in range(0, len(texts), COHERE_MAX_TEXTS_PER_CALL):
        chunk = texts[i:i + COHERE_MAX_TEXTS_PER_CALL]
        body = json.dumps({
            "texts": chunk,
            "input_type": input_type,
            # Cohere caps each individual text at ~2048 characters; truncate from the end rather than raising an error if a chunk ever comes in longer than that.
            "truncate": "END",
        })
        response = bedrock_client.invoke_model(
            modelId=COHERE_MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        embeddings.extend(result["embeddings"])

    return embeddings if is_batch else embeddings[0]
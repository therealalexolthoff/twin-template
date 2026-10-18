# Function for embedding using Google's embedding model
import math
import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import EmbedContentConfig

load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.environ.get("PROJECT_ID", "digital-twin-template"),
    location=os.environ.get("LOCATION", "us-central1"),
)


def _normalize(vector):
    # gemini-embedding-001 only returns unit-length vectors at its full 3072
    # dimensions. At 256 they have to be normalized here, so that every vector
    # is compared on direction alone.
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector] if norm else vector


def run_embeddings(texts, task_type):
    # gemini-embedding-001 only accepts one input per request, so this makes
    # one call per text. Accepts a single string or a list of strings, and
    # always returns a list of vectors in the same order.
    if isinstance(texts, str):
        texts = [texts]

    vectors = []
    for i, text in enumerate(texts, start=1):
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=EmbedContentConfig(output_dimensionality=256, task_type=task_type),
        )
        vectors.append(_normalize(response.embeddings[0].values))
        if len(texts) > 1:
            print(f"Embedded {i}/{len(texts)}")
    return vectors

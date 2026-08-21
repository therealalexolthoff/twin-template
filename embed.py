# Function for embedding using Google's embedding model
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
 
 
def run_embeddings(input, task_type):
    response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=input,
                config=EmbedContentConfig(output_dimensionality=256, task_type=task_type)
            )
    return [item.values for item in response.embeddings]
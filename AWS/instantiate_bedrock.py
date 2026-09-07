import os
import boto3
# Model and region are configurable via env vars so this can be swapped without touching code (e.g. moving between Claude, Titan, or another Bedrock-hosted model, or a different AWS region than your instance's default).
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
)
BEDROCK_REGION = os.environ.get(
    "BEDROCK_REGION", os.environ.get("AWS_REGION", "us-east-1")
)

bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
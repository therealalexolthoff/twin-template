from botocore.exceptions import ClientError
from context import system_prompt, get_context
from instantiate_bedrock import bedrock_client, BEDROCK_MODEL_ID

# Gradio can hand back either a plain string or a list of typed content parts, depending on the message. This normalizes either shape down to plain text.
def extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return str(content)


def respond_basic(message, history):
    # Retrieve RAG context for the turn
    context = get_context(message)

    # Bedrock's Converse API expects roles to be exactly "user" or "assistant" very similar to the openai package. However, you'll notice that bedrock also expects that content will be a list a nested dictionary, and within the dictionary a series a key of "text" and then the message from a given turn. This dictionary can serve as a container for multi-modal messages, so it could also contain a key for "image" and a value of an image file, or a key of "audio", "video", or "document", depending on the file type.
    messages = []
    for msg in history:
        role = "assistant" if msg["role"] == "assistant" else "user"
        text = extract_text(msg["content"])
        if text:
            messages.append({"role": role, "content": [{"text": text}]})

    messages.append({"role": "user", "content": [{"text": extract_text(message)}]})

    try:
        response_stream = bedrock_client.converse_stream(
            modelId=BEDROCK_MODEL_ID,
            messages=messages,
            system=[{"text": system_prompt() + context}],
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0.7,
                "topP": 0.9,
            },
        )
    except ClientError as e:
        # Show a message to show the user if there is an error. There are three potential cases: 1. the user sends an oddly-formatted message (this never happens). 2. Bedrock access is restricted for some reason. or 3. A general catch-all issue.
        error_code = e.response["Error"]["Code"]
        if error_code == "ValidationException":
            yield f"Something went wrong formatting that request for the model. ({e})"
        elif error_code == "AccessDeniedException":
            yield (
                "This app doesn't have access to the configured Bedrock model yet."
                "Check that model access is enabled for it in the Bedrock console"
                "for this region."
            )
        else:
            yield f"Something went wrong talking to Bedrock: {e}"
        return

    # Converse_stream returns an event stream. text arrives incrementally inside contentBlockDelta events, mirroring the token-by-token streaming the Gradio UI expects.
    partial = ""
    for event in response_stream["stream"]:
        delta = event.get("contentBlockDelta", {}).get("delta", {})
        if "text" in delta:
            partial += delta["text"]
            yield partial
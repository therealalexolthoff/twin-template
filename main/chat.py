import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from main.context import system_prompt, get_context
from main.tools import tools, FUNCTION_MAP

# Loads variables from a local .env file, if one exists. In Cloud Run the
# real env vars are already set on the container, so this is a harmless
# no-op there — load_dotenv() doesn't overwrite existing env vars.
load_dotenv()

# This sets up a connection to GCP's vertexai, now called Gemini Enterprise Agent Platform. The location is not a specific region like us-east1 or us-central1, but instead needs to operate across a larger region (us or eu). The project refers to the project-id.

client = genai.Client(
    vertexai=True,
    project=os.environ.get("PROJECT_ID", "digital-twin-template"),
    location=os.environ.get("CHAT_LOCATION", "us"),
)

#limits number of tool calls to 5
MAX_TOOL_ROUNDS = 5


# This removes the text from the gradio dictionary
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


def _run_function_calls(function_calls):
    response_parts = []
    for fc in function_calls:
        func = FUNCTION_MAP.get(fc.name)
        if func is None:
            result = f"Unknown function: {fc.name}"
        else:
            try:
                result = func(**(fc.args or {}))
                print(result)
            except Exception as e:
                result = f"Error running {fc.name}: {e}"
        response_parts.append(
            types.Part.from_function_response(
                name=fc.name,
                response={"result": result},
            )
        )
    return response_parts


def respond_basic(message, history):
    # When using vertex, you need to give it a list (like the messages used in openai's chat completions. However, unlike the messages in openai's chat completions, here we are using google's types module to leverage built-in classes. an instance of the Content class is roughly equivalent to a dictionary {"role": role, "content": "This is a message"}. However, you'll notice that instead of using the "content": "Some text for the message", Gemini wants parts= and then a list of instances of Part. This is because Gemini here needs you to specify that each part of a given message is of a specific type, either file or text.
    context = get_context(message)
    vertex_history = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        text = extract_text(msg["content"])
        if text:
            vertex_history.append(
                types.Content(role=role, parts=[types.Part(text=text)])
            )

    # Here Gemini is being called similarly to how the openai sdk uses chat completions. Notice that instead of having the system prompt in the summary, it is added as a separate item inside the config parameter, as the system_instruction. thinking_config allows you to set the reasoning effort of the model.
    print(context)
    chat = client.chats.create(
        model="gemini-3.5-flash-lite",
        history=vertex_history,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt() + context,
            thinking_config=types.ThinkingConfig(thinking_level="low"),
            tools=tools,
            # No automatic_function_calling here: our tools are built from
            # FunctionDeclaration (custom descriptions/schemas), not raw
            # Python callables, so the SDK has no function to auto-invoke.
            # We handle function calls ourselves in the loop below instead.
        ),
    )

    partial = ""
    next_message = extract_text(message)

    for _ in range(MAX_TOOL_ROUNDS):
        function_calls = []
        for chunk in chat.send_message_stream(next_message):
            if chunk.text:
                partial += chunk.text
                yield partial
            if chunk.function_calls:
                function_calls.extend(chunk.function_calls)

        if not function_calls:
            break

        next_message = _run_function_calls(function_calls)
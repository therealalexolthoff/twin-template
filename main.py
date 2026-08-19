import os
import gradio as gr
from google import genai
from google.genai import types
from context import system_prompt, topic_context

# This sets up a connection to GCP's vertexai, now called Gemini Enterprise Agent Platform. The location is not a specific region like us-east1 or us-central1, but instead needs to operate across a larger region (us or eu). The project refers to the project-id.

client = genai.Client(
    vertexai=True,
    project="digital-twin-template",
    location="us",
)

#This removes the text from the gradio dictionary  
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
    # When using vertex, you need to give it a list (like the messages used in openai's chat completions. However, unlike the messages in openai's chat completions, here we are using google's types module to leverage built-in classes. an instance of the Content class is roughly equivalent to a dictionary {"role": role, "content": "This is a message"}. However, you'll notice that instead of using the "content": "Some text for the message", Gemini wants parts= and then a list of jnstances of Part. This is because Gemini here needs you to specify that each part of a given message is of a specific type, either file or text.)
    vertex_history = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        text = extract_text(msg["content"])
        if text:
            vertex_history.append(
                types.Content(role=role, parts=[types.Part(text=text)])
            )
    # Here Gemini is being called similarly to how the openai sdk uses chat completions. Notice that instead of having the system prompt in the summary, it is added as a separate item inside the config paramater, as the system_instruction. thinking_config allows you to set the reasoning effort of the model.
    chat = client.chats.create(
        model="gemini-3.5-flash-lite",
        history=vertex_history,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt(),
            thinking_config=types.ThinkingConfig(thinking_level="low"),
        ),
    )

    partial = ""
    for chunk in chat.send_message_stream(extract_text(message)):
        if chunk.text:
            partial += chunk.text
            yield partial


gr.ChatInterface(fn=respond_basic).launch()
#imports
import os 
from openai import OpenAI
from dotenv import load_dotenv
import gradio as gr
from context import system_prompt, topic_context

load_dotenv()
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
client = OpenAI()

def improve_context(message):
    system_message = system_prompt()
    target = system_message.rfind("???")
    for k,c in topic_context.items():
        if k in message:
            system_message = system_message[:target] + c + system_message[target:]
    return system_message
            


def respond_basic(message,history):
    system_message = improve_context(message)
    messages = [{"role": "system", "content": system_message}] +  history + [{"role": "user", "content": message}]
    response = client.chat.completions.create(
        messages = messages,
        model="gpt-4.1-mini"
    )
    return response.choices[0].message.content

gr.ChatInterface(fn=respond_basic).launch()

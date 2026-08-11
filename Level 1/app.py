#imports
import os 
from openai import OpenAI
from dotenv import load_dotenv
import gradio as gr
from context import system_prompt

load_dotenv()
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
client = OpenAI()


def respond_basic(message,history):
    messages = [{"role": "system", "content": system_prompt()}] +  history + [{"role": "user", "content": message}]
    response = client.chat.completions.create(
        messages = messages,
        model="gpt-4.1-mini"
    )
    return response.choices[0].message.content

gr.ChatInterface(fn=respond_basic).launch()

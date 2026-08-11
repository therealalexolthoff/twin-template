#imports
import os 
from openai import OpenAI
from dotenv import load_dotenv
import gradio as gr

load_dotenv()
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
client = OpenAI()


def system_prompt():
    return """
              You are the digital twin of a person. Your job is to answer questions as that person. That person is named 'Person'. 
              
              IMPORTANT!!! 
              DO NOT MAKE UP INFORMATION. ALL INFORMATION ABOUT Person IS BETWEEN THE STARTING AND CLOSING THREE ? SYMBOLS.

              IF THE INFORMATION IS NOT BETWEEN THE THREE ? SYMBOLS, SAY 'I Don't Know About That'.
              
              ???
              Person works full time in a job in an industry, and has a number of years 
              of experience. 
              
              
              Person has skills, education, and qualifications.

              Person also has a few hobbies. They include hobby 1, hobby 2, and hobby 3. Person 

              Person has goals. They include both professional and personal goals. Person's professional goals are goal 1, goal 2, goal 3. Person's personal goals are goal 4, goal 5, and goal 6. 

              Person communicates in a style. Answer all questions in that style.
              ???
              
        """

def respond_basic(message,history):
    messages = [{"role": "system", "content": system_prompt()}] +  history + [{"role": "user", "content": message}]
    response = client.chat.completions.create(
        messages = messages,
        model="gpt-4.1-mini"
    )
    return response.choices[0].message.content

gr.ChatInterface(fn=respond_basic).launch()

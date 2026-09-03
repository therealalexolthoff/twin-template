import os
import gradio as gr
from chat import respond_basic
 
if __name__ == "__main__":
    # 0.0.0.0 + $PORT is what Cloud Run expects a service to bind to.
    # Locally, PORT is unset so this falls back to Gradio's usual 8080.
    gr.ChatInterface(fn=respond_basic).launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 8080)),
    )
 
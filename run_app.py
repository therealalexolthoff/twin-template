import os
import gradio as gr
from main.chat import respond_basic

if __name__ == "__main__":
    # 0.0.0.0 + $PORT is what Cloud Run expects a service to bind to.
    # Locally, PORT is unset so this falls back to Gradio's usual 8080.
    # footer_links=[] hides the "Use via API" link; analytics_enabled=False
    # stops Gradio from sending usage stats.
    gr.ChatInterface(fn=respond_basic, analytics_enabled=False).launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 8080)),
        share=False,
        footer_links=[],
        allowed_paths=[],
    )

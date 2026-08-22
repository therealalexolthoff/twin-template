# AI Chatbot Template
**A Production-Ready Template**
 
This project is for those looking for a plug-and-play AI-powered chatbot. Whatever your use case, whether to represent yourself professionally or to provide a chatbot to end-users focused on answering questions in a specific domain, this is for you. Our promise is simple: you plug in your data, and you get a secure, scalable, simple-to-deploy chatbot that will run at little to no cost.
 
## Background of the Project
 
This project was created in response to Hugging Face's abrupt decision to charge new users for Spaces that use the Gradio SDK.
 
One member of the Hugging Face community put together a great [list of alternatives](https://discuss.huggingface.co/t/official-community-complaint-revert-free-cpu-basic-spaces-and-remove-anti-developer-sdk-restrictions/177703/10#p-260365-h-1-streamlit-community-cloud-streamlitiocloud-1) for hosting a digital twin/chatbot, but none of them are built for scalable, out-of-the-box use. Instead, they're primarily hosting solutions like Hugging Face. But you'll still have to write all the code to make the hosting work, and it may or may not scale well, be secure, or have the functionality you want.
 
With this project, we aim to address all those concerns, so that all you need to do is follow the steps in the Deployment guide and you'll have your own production build ready in less than a day.
 
## Notes on Architecture
 
We built this template using Gradio for the interface and Gemini via Vertex AI for both the chatbot's responses and the retrieval that grounds them in your own documents. A lightweight embedded vector database (Chroma) holds the knowledge base, so there's no separate database service to run or pay for. On GCP, this splits into two small pieces: a Cloud Run Job that builds the knowledge base from your documents, and a Cloud Run service that serves the chatbot itself — both set up to deploy with as little work as possible.
 
As the project develops, we'll update this section and the deployment guide to reflect changes.
 


















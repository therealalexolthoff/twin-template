# AI ChatBot Template
 
## A Production-Ready Template
 
This project is for those looking for a plug and play AI-Powered Chat Bot. Whatever your use case, whether to represent yourself professionally, or provide a chatbot to end-users focused on answering questions in a specific domain, this is for you. Our promise is simple: You plug in your data, and you get a secure, scalable, simple to deploy chatbot that will run at a little to no cost.


## Background of The Project
 
This project was created in response to HuggingFace's abrupt decision to charge new users for Spaces that use the Gradio SDK.
 
One member of the HuggingFace community put together a great [list of alternatives](https://discuss.huggingface.co/t/official-community-complaint-revert-free-cpu-basic-spaces-and-remove-anti-developer-sdk-restrictions/177703/10#p-260365-h-1-streamlit-community-cloud-streamlitiocloud-1) for hosting a digital twin/chatbot, but none of them are built for scalable, out of the box use. Instead, they're primarily hosting solutions like HuggingFace. But you'll still have to write all the code to make the hosting work, and it may or may not scale well/be secure/have the functionality you want.

With this project, we aim to address all those concerns, so that all you need to do is follow the steps in the guide Deploy.md and you'll have your own production build ready in less than 1 day.


### Notes on Architecture

We built this template using gradio, the OpenAI sdk with chat completions, and set up the architecture to deploy to GCP's Cloud Run with as little work as possible.

As the project develops, we'll update this section and the "How To Deploy" guide to reflect changes.
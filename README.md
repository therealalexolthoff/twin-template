# Digital Twin Template

## A Learning Ladder And Production-Ready Template

This project is for 2 audiences:

1. People who want a step-by-step, structured process for learning AI Engineering skills and deploying an AI Engineering project to one of the major cloud platforms for free/extremely little money.

2. Existing tech professionals who want a RAG-powered chat interface that uses MCP for tool calling, can run for very little money, can be embedded, and requires minimal configuration.

If that's you, welcome! We're glad you stopped by.

## Quickstart

Want to skip right to deploying the your digital twin to production? Check out "DeployingToGCP.md" in the LevelGuides/Level3 folder.

## How To Use This Project

If you are completely new to AI Engineering, this project can help you learn many of the fundamental concepts of the discipline while also providing you with the skills and knowledge required to deploy a production-grade AI Engineering project that real end-users can interact with. You can learn these skills, for free, and deploy your own production-grade AI Engineering project, for free (or incredibly cheap), by following the guides and working your way through the sub projects, starting at Level 0 and working your way up to Level 20. 

As of today, there are only 3 levels. We will update this guide every few days with additional levels, so check back often!

### COMING SOON
If you don't care about learning right now and just want an AI powered chatbot that you can embed on an existing website or use on a standalone website, you can skip directly to the Level 20, follow the associated guide, and have your chatbot ready in under an hour. Our goal for you is that you bring the tools and data, plug it in to the chatbot, deploy, and let users start interacting, all as quickly as possible.

## Expectations For Learners

If you've decided to work your way through the Levels from 0, please note the following expectations:

1. We expect you to know basic Python. By basic, we mean you can write functions and loops, understand what an object is, and are comfortable manipulating lists and dictionaries. You do not need to be proficient in OOP, and you do not need to understand decorators, async functions, or how to work with python libraries like pytorch, pandas, or tensorflow. 
2. You are not afraid of the terminal. Starting in level 1, you will be expected to use the terminal integrated into Cursor or VS Code. 
3. You use AI to help you work through weird situations, but not to learn core concepts. It is likely you will run into problems: maybe GCP introduces a breaking change to its CLI tool, and one of the commands in a guide fails because the name of a flag changed. If you encounter a breaking change, go ask Claude about it, solve the problem, and make a PR on the Guide to address the breaking change. 

But don't use Claude to explain what vector embeddings are, or how to deploy to GCP. Use the guides, and if necessary, the docs we provide you. Using AI for "learning" core competencies won't help you retain the information. Instead, it will give you a feeling of learning that will vanish the moment you can no longer ask AI for clarification. In short, outsource some of you problem solving,not your understanding.

## Background of The Project

This project was created in response to HuggingFace's abrupt decision to charge users for Spaces that use the Gradio SDK.

One member of the HuggingFace community created a great  [list of alternatives](https://discuss.huggingface.co/t/official-community-complaint-revert-free-cpu-basic-spaces-and-remove-anti-developer-sdk-restrictions/177703/10#p-260365-h-1-streamlit-community-cloud-streamlitiocloud-1) you can use to host a digital twin/chat bot, but none of these alternatives provide guides on *AI Engineering*, and very few of them could be used in a professional setting. 

We decided to try to find an alternative path and platform that would turn novices, like ourselves when we started using HuggingFace Spaces, into a confident practitioner.

To do this, we asked a few key questions:

1. What skills, tools, and technologies are essential to know in order to call oneself an "AI Engineer"?
   A quick compendium includes intermediate fluency with and ability to deploy to at least one of the major cloud platform (GCP, Azure, or AWS), tool calling, using MCP, setting up RAG pipelines, additional context engineering, competency with Terraform for cloud infrastructure management, comfort with the CLI, and 

2. Which major cloud platform was going to offer the best balance of cheap and easy to configure services?
    We eventually settled on GCP: CloudRun, Secret Manager, and Firestore (for RAG) can be used for free unless the twin sees exceptionally large volumes of traffic. More details about the project architecture will be documented in a technical decisions guide (coming soon). 

    In addition, GCP's sign up experience, console, and CLI are all user friendly enough for a novice to pick up.

3. What does a logical learning progression look like? 
   Several of the resources we consulted when learning AI engineering introduced Tool Calling, Agents, and other concepts early, and none taught deployment to any of the major cloud services. In fact, cloud deployment, if it was taught, was treated as a completely separate subject/course, walled off from content about AI Engineering.

   We believe this is a mistake: AI Engineering, as a discipline, requires a clear understanding of deployment, including managing scalability, reliability, and cost management. Unlike traditional web or app development, AI Engineers must carefully consider these cloud concepts as early as possible because the systems they build, and the way they build them, will have a huge impact on their wallet. After all, every time an end user or engineer interacts with an LLM through an API, there is a cost. Learning to understand how that works in production, and how to manage it well, is not something that can wait.

   For this reason, we favor a learning structure where for every 2 "core AI Engineering" levels, there is one level on deployment. This helps learners quickly get comfortable with GCP as they learn, and connect the AI Engineering concepts to cloud deployment, rather than treating them as two isolated subjects.

   In practice, this means waiting to learn tool calling until after learning RAG and Docker. While Tool Calling is arguably *simpler* and perhaps a more fundamental AI Engineering concept, we believe an AI Engineer who can deploy a RAG pipeline to GCP without any tool calling is more valuable than an AI Engineer who knows how to call tools but can't deploy to production. We also believe that learning deployment in smaller doses sooner in the learning process helps AI Engineers avoid being overwhelemed by the supposed complexity of deployment when they learn it as a separate subject.


# Digital Twin Template
 
## A Learning Ladder And Production-Ready Template
 
This project is for 2 audiences:
 
1. People who want a step-by-step, structured process for learning AI Engineering skills and deploying an AI Engineering project to one of the major cloud platforms for free/very little money.
2. Existing tech professionals who want a RAG-enabled chat interface that uses MCP for tool calling, can run for free/very little money, can be embedded on an existing website, and requires minimal configuration. (Set up guide coming soon!)
If that's you, welcome! We're glad you stopped by.
 
## Quickstart
 
Want to skip right to deploying your digital twin to production? Check out `DeployingToGCP.md` in the `LevelGuides/Level3` folder.
 
*(A faster, low-code path in Level 20 is planned but not live yet. Once it's ready, it'll let you plug in your own tools and data and deploy a chatbot in under an hour, no need to work through the earlier levels first. Check back soon.)*
 
## How To Use This Project
 
If you are completely new to AI Engineering, this project can help you learn many of the fundamental concepts of the discipline while also providing you with the skills and knowledge required to deploy a production-grade AI Engineering project that real end-users can interact with. You can learn these skills for free, and deploy your own production-grade AI Engineering project for free (or incredibly cheap), by following the guides and working your way through the sub-projects, starting at Level 0 and working your way up.
 
As of today, there are only 3 levels (0–3). We'll add new levels every few days, so check back often.
 
## Expectations For Learners
 
If you've decided to work your way through the levels from 0, please note the following expectations:
 
1. **You know basic Python.** By basic, we mean you can write functions and loops, understand what an object is, and are comfortable manipulating lists and dictionaries. You do not need to be proficient in OOP, and you do not need to understand decorators, async functions, or how to work with Python libraries like PyTorch, pandas, or TensorFlow.
2. **You're not afraid of the terminal.** Starting in Level 1, you'll be expected to use the terminal integrated into Cursor or VS Code.
3. **You use AI to help you work through weird situations, not to learn core concepts.** It's likely you'll run into problems — maybe GCP introduces a breaking change to its CLI tool, and one of the commands in a guide fails because a flag name changed. If you hit a breaking change, ask Claude about it, solve the problem, and open a PR on the guide to address it.
   But don't use Claude to explain what vector embeddings are, or how to deploy to GCP. Use the guides, and if necessary, the doc links we've included in them. Using AI to "learn" core competencies won't help you retain the information — it will give you a feeling of learning that vanishes the moment you can no longer ask AI for clarification. In short: outsource some of your problem solving, not your understanding.
## Background of The Project
 
This project was created in response to HuggingFace's abrupt decision to charge new users for Spaces that use the Gradio SDK.
 
One member of the HuggingFace community put together a great [list of alternatives](https://discuss.huggingface.co/t/official-community-complaint-revert-free-cpu-basic-spaces-and-remove-anti-developer-sdk-restrictions/177703/10#p-260365-h-1-streamlit-community-cloud-streamlitiocloud-1) for hosting a digital twin/chatbot, but none of them come with guides on *AI Engineering*, and very few could be used in a professional setting.
 
We decided to find an alternative path and platform that would turn novices — like ourselves when we started using HuggingFace Spaces — into confident practitioners.
 
To do this, we asked a few key questions:
 
**1. What skills, tools, and technologies are essential to know in order to call oneself an "AI Engineer"?**
 
A quick compendium includes intermediate fluency with, and the ability to deploy to, at least one of the major cloud platforms (GCP, Azure, or AWS); tool calling; using MCP; setting up RAG pipelines; additional context engineering; competency with Terraform for cloud infrastructure management; and comfort with the CLI.
 
**2. Which major cloud platform offers the best balance of cheap and easy to configure?**
 
We settled on GCP: Cloud Run, Secret Manager, and Firestore (for RAG) can all be used for free unless the twin sees exceptionally large volumes of traffic. More details on the project architecture will be documented in a technical decisions guide (coming soon).
 
GCP's sign-up experience, console, and CLI are also user-friendly enough for a novice to pick up.
 
**3. What does a logical learning progression look like?**
 
Several of the resources we consulted when learning AI Engineering introduced Tool Calling, Agents, and other concepts early, and none taught deployment to any of the major cloud services. When cloud deployment was taught at all, it was treated as a completely separate subject, walled off from the AI Engineering content.
 
We believe this is a mistake: AI Engineering, as a discipline, requires a clear understanding of deployment, including managing scalability, reliability, and cost. Unlike traditional web or app development, AI Engineers must consider these cloud concepts as early as possible, because the systems they build — and the way they build them — have a real impact on their wallet. Every time an end user or engineer interacts with an LLM through an API, there's a cost. Learning how that works in production, and how to manage it well, isn't something that can wait.
 
For this reason, we favor a learning structure where, for every 2 "core AI Engineering" levels, there's one level on deployment. This helps learners get comfortable with GCP as they learn, and connects AI Engineering concepts to cloud deployment rather than treating them as two isolated subjects.
 
In practice, this means waiting to learn tool calling until after learning RAG and Docker. While tool calling is arguably *simpler*, and perhaps a more fundamental AI Engineering concept, we believe an AI Engineer who can deploy a RAG pipeline to GCP without any tool calling is more valuable than one who knows how to call tools but can't deploy to production. We also believe that learning deployment in smaller doses, earlier in the process, helps AI Engineers avoid feeling overwhelmed by the supposed complexity of deployment when it's taught as a separate subject later on.
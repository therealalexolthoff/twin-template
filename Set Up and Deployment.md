# A Simple Guide For Setting Up and Deploying The Digital Chatbot

## Pre-Req for Everything Else

Fork this repository into your own GitHub account. You'll need your own copy of it for deployment, and making a fork is the easiest way to do so.

## Local Set Up

If you want to test the chatbot on your local computer, you'll need to install it locally.

Start by running `git clone https://github.com/{YOUR-GITHUB-USERNAME}/twin-template`

To set up this project environment locally, we recommend using uv. 

Once you have uv installed, just run `uv run main.py`. This will create a virtual environment, install dependencies, and create a server to test the project locally. 

## Deployment

The project is already set up to deploy on GCP Cloud Run. 

If you do not have a GCP account, [sign up for an account](https://cloud.google.com/free). 

You are welcome to deploy on any other cloud platform of your choice, but we strongly recommend GCP for reasons documented in [Architectural Justifications](architectural-justifications.md).

Once your account is created, you'll need to provide a payment method. You'll then be redirected to a project page, where you can configure your project.

Now you'll be able to follow the steps below.

 
## Part 1 — Personalize your chatbot
 
The template comes with placeholder information in `context.py`. You can edit it right in your browser:
 
1. In your forked repo, click **context.py** to open it.
2. Click the **pencil (edit) icon** in the top-right of the file view.
3. Replace the placeholder details between the `???` markers with real information about yourself, and update the `topic_context` dictionary entries the same way. Make sure you also replace the information above the `???` with your name and other relevant information about yourself.
4. Scroll down and click **Commit changes**.
`main.py` and `requirements.txt` are already set up correctly in the template — you don't need to touch them.
 
## Part 2 — Store your OpenAI key in Secret Manager
 
1. In the [Google Cloud Console](https://console.cloud.google.com), search **Secret Manager** in the top search bar and open it.
2. Click **Create Secret**.
3. Name it `openai-api-key`, paste your actual key into the **Secret value** field, and click **Create Secret**.
4. Note your project number — it's shown in the **Project info** card on the console's **Home/Dashboard** page. You'll need it in Part 5.
> **Why not just paste the key into Cloud Run directly?** Secret Manager keeps it out of deployment logs, revision history.
 
## Part 3 — Create the Cloud Run service, connected to your fork
 
1. Search **Cloud Run** and click **Create Service**.
2. Choose **"Continuously deploy new revisions from a source repository."**
3. Click **Set up with Cloud Build**. Choose **GitHub** as the provider, click **Authenticate**, and approve the Google Cloud Build GitHub app (a one-time authorization popup).
4. Select your **forked repository**. It will look like this: https://github.com/{YOUR-GITHUB-USERNAME}/twin-template. If it's not listed, click **Manage connected repositories** and grant the GitHub app access to it.
5. Under **Build Type**, choose **Google Cloud Buildpacks**. Click **Save**.
6. Pick a **region** (e.g. `us-central1`). If it's important to you that the chatbot load quickly in your area, you can use [this site](https://gcping.com/) and choose the region at the top of the list after waiting about 1 minute. This is the closest region to you, and it will guarantee that the chatbot always loads at the top speed.
7. Under **Authentication**, choose **Allow unauthenticated invocations** so the app is publicly reachable.
8. Expand **Container, Networking, Security**, open the **Variables & Secrets** tab, and click **Reference a secret**. Set:
   - **Name:** `OPENAI_API_KEY`
   - **Secret:** `openai-api-key`
   - **Version:** `latest`
9. Click **Create**. Approve any prompts to enable APIs (Cloud Build, Artifact Registry) along the way.
 
## Part 4 — Let Cloud Run actually read the secret
 
Referencing the secret in Part 4 doesn't automatically grant permission to read it. That's a separate, one-time step:
 
1. Use the search function on the dashboard to navigate to **IAM & Admin → IAM**.
2. Click **Grant Access**.
3. In **New principals**, paste:
```
   YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com
```
   (using the project number from Part 3)
4. For **Role**, choose **Secret Manager Secret Accessor**.
5. Click **Save**.
 
---
 
## Part 5 — Watch it build, then test it
 
A build kicks off automatically once the service is created, and usually takes 2–4 minutes. When it finishes, click the **URL** near the top of the Cloud Run service page — that's your live, personalized chat bot.
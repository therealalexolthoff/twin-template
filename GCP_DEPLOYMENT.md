# A Simple Guide For Setting Up and Deploying Your AI Chatbot

## Pre-Requisites

1. A Google Cloud Platform Account. If you decide to host on another platform, this will not be useful to you. If you have an older Google Cloud Platform account, we recommend creating a new one to take advantage of the $300 usage credits, which will keep your costs at 0 for the first three months.
2. UV installed on your computer. If you don't have uv installed, follow the guide here: https://docs.astral.sh/uv/.
   
## Local Setup

If you want to test the chatbot on your local computer, you'll need to install it locally.

Start by running `git clone https://github.com/{YOUR-GITHUB-USERNAME}/twin-template`.

Once it's cloned, complete the following steps,

1. Install the gcloud cli tool (follow the guides on this page) https://docs.cloud.google.com/sdk/docs/install-sdk#mac.
2. Run `gcloud auth application-default login` once — this lets the project talk to Vertex AI from your own machine the same way it will from Cloud Run.
3. Create a `.env` file in the repo root containing `PROJECT_ID=your-project-id`.
4. Run `uv run run_ingest.py`. This builds a local knowledge base from the `.txt` files in `rag_data/` — nothing gets uploaded anywhere yet, it just creates a `chroma_db/` folder on your machine.
5. Run `uv run run_app.py`. This installs dependencies, creates a virtual environment, and starts a local server so you can chat with your twin before deploying it.

## Deployment

The project is already set up to deploy on GCP Cloud Run.

If you do not have a GCP account, [sign up for an account](https://cloud.google.com/free).

You are welcome to deploy on any other cloud platform of your choice, but we strongly recommend GCP for reasons documented in [Why We Recommend GCP](ARCHITECTURE.md).

Once your account is created, you'll need to provide a payment method. You'll then be redirected to a project page, where you can configure your project.

Now you'll be able to follow the steps below. There are more of them than you might expect for a chatbot — that's because this version doesn't just answer from a fixed script, it actually retrieves from your own documents before answering, which means there's a small pipeline to set up alongside the chatbot itself.

## Part 1 — Personalize your chatbot

1. In your forked repo, open the `main/` folder and click **context.py** to open it.
2. Click the **pencil (edit) icon** in the top-right of the file view.
3. Replace the placeholder details in `system_prompt()` with real information about yourself — your name, what you do, your skills, hobbies, goals, and how you communicate.
4. Scroll down and click **Commit changes**.
5. Now add your actual knowledge base: in the `rag_data/` folder, add `.txt` files with whatever information you want your twin to be able to answer questions about — your résumé, blog posts, notes about your projects, anything. Use GitHub's **Add file → Create new file** button for each one.

Everything else — `main/chat.py`, `ingest/chunker.py`, `shared/embed.py`, `pyproject.toml`, and so on — is already set up correctly in the template — you don't need to touch them.

## Part 2 — Create your two Cloud Storage buckets and upload your documents

The chatbot needs two Cloud Storage buckets: one holding your source documents, and one holding the search index built from them.

1. Search **Cloud Storage** and click **Create bucket**.
2. Name it something like `your-project-id-twin-docs`. Pick a region — you'll reuse this same region for everything else in this guide, so it's worth writing down.
3. Leave the other settings as default and click **Create**.
4. Open the bucket and click **Upload files**. Select every `.txt` file from your local `rag_data/` folder.
5. Repeat steps 1–3 to create a second bucket, named something like `your-project-id-twin-index`. Leave it empty for now — the ingestion job fills it in Part 5.

> **Why two buckets instead of one?** One holds your raw documents, which only the ingestion job needs to read. The other holds the finished search index, which is all the chatbot itself ever touches. Keeping them separate means the live chatbot never needs permission to read your source files directly.

## Part 3 — Give your project permission to use Vertex AI and your buckets

Unlike many AI APIs, there's no API key to create or store here — Vertex AI authenticates through Google Cloud's own permission system (IAM), using the identity already attached to whatever's making the request. That identity just needs to be told it's allowed to do a few things.

1. Note your project number — it's shown in the **Project info** card on the console's **Home/Dashboard** page.
2. Use the search bar to navigate to **IAM & Admin → IAM**.
3. Click **Grant Access**.
4. In **New principals**, paste:
   ```
   YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com
   ```
5. For **Role**, choose **Vertex AI User**, then click **+ Add another role** and also add **Storage Object Admin**, then once more to add **Model Armor User**.
6. Click **Save**.

> **Why Storage Object Admin on IAM, rather than per-bucket?** It's simpler for a personal project to grant it once at the project level. If you'd rather scope it tightly to just these two buckets, you can instead open each bucket's **Permissions** tab and grant access there individually — either works.

## Part 3.5 — Set up Model Armor

Every message a user sends is screened by Model Armor before it reaches Gemini, so attempts to jailbreak the chatbot or inject instructions get rejected. This needs a Model Armor template the chatbot can check prompts against.

1. Search **Model Armor** and enable the Model Armor API if prompted.
2. Click **Create template**.
3. Template ID: `twin-model-armor`. Region: `us-east4`. These are the defaults the chatbot looks for — if you pick a different ID or region, set `MODEL_ARMOR_TEMPLATE` and/or `MODEL_ARMOR_LOCATION` on the service in Part 6.
4. Turn on **Prompt injection and jailbreak detection**, plus any other filters you want, then click **Create**.

## Part 4 — Connect your repo and build both container images

This chatbot ships as two separate pieces: a job that builds the knowledge base, and a service that chats using it. Each has its own Dockerfile (`Dockerfile.ingest` and `Dockerfile.serve`), so this part builds both.

1. Search **Cloud Build** and open **Triggers**.
2. Click **Connect Repository**, choose **GitHub**, click **Authenticate**, and approve the Google Cloud Build GitHub app (a one-time authorization popup).
3. Select your **forked repository**. If it's not listed, click **Manage connected repositories** and grant the GitHub app access to it.
4. Click **Create Trigger**:
   - Name: `build-twin-ingest`
   - Event: **Manual invocation**
   - Source: your repo, branch `main`
   - Configuration: **Dockerfile**
   - Dockerfile name: `Dockerfile.ingest`
   - Image name: pick an Artifact Registry path, e.g. `us-central1-docker.pkg.dev/YOUR_PROJECT_ID/twin-repo/twin-ingest` (the first time you do this, Cloud Build will offer to create the `twin-repo` Artifact Registry repository for you — accept it)
   - Save
5. Create a second trigger the same way:
   - Name: `build-twin-serve`
   - Dockerfile name: `Dockerfile.serve`
   - Image name: `us-central1-docker.pkg.dev/YOUR_PROJECT_ID/twin-repo/twin-serve`
   - Save
6. On the Triggers list, click **Run** (⋮ menu) on `build-twin-ingest`, then again on `build-twin-serve`. Watch both under **Cloud Build → History** until they show green checkmarks.

## Part 5 — Create and run the ingestion job

This is the piece that actually reads your documents, turns them into a searchable index, and saves that index to your index bucket.

1. Search **Cloud Run**, click **Jobs**, then **Create Job**.
2. Container image URL: browse to the `twin-ingest` image you just built.
3. Job name: `twin-ingest-job`. Region: the same one you used for your buckets.
4. Under **Variables & Secrets**, add:
   - `PROJECT_ID` = your project ID
   - `LOCATION` = your region (e.g. `us-central1`)
   - `DOCS_BUCKET` = your docs bucket name
   - `INDEX_BUCKET` = your index bucket name
5. Under **Containers → Resources**, set memory to at least 2 GiB, and under **Task timeout**, set something generous like 60 minutes.
6. Click **Create**, then open the job and click **Execute**.
7. Watch the **Logs** tab until it finishes, then check your index bucket in Cloud Storage — you should see a `chroma_db/` folder appear.

## Part 6 — Create the chatbot service

1. Go back to **Cloud Run** and click **Create Service**.
2. Choose **Deploy one revision from an existing container image**, and browse to the `twin-serve` image.
3. Service name: `twin-serve`. Region: the same one as everything else.
   > If it's important to you that the chatbot load quickly in your area, you can use [this site](https://gcping.com/) and choose the region at the top of the list after waiting about 1 minute. That's the closest region to you, and it will guarantee the chatbot always loads at top speed.
4. Under **Authentication**, choose **Allow unauthenticated invocations** so the app is publicly reachable.
5. Under **Variables & Secrets**, add:
   - `PROJECT_ID` = your project ID
   - `LOCATION` = your region
   - `CHAT_LOCATION` = `us` (or `eu` if you're in Europe) — this is a separate setting from `LOCATION` above, because the chat model runs on a different kind of region than the embedding model does
   - `INDEX_BUCKET` = your index bucket name
   - Optional, only if your Model Armor template from Part 3.5 doesn't use the defaults:
     - `MODEL_ARMOR_LOCATION` = the template's region (default `us-east4`)
     - `MODEL_ARMOR_TEMPLATE` = the template ID (default `twin-model-armor`)
   - Optional, to let the chatbot email you messages from visitors (via [Resend](https://resend.com)):
     - `RESEND_API_KEY` = your Resend API key
     - `NOTIFY_EMAIL` = the address the messages should go to
     - `RESEND_FROM` = the sender, e.g. `Your Name Twin <onboarding@resend.dev>`
6. Under **Containers → Resources**, set memory to at least 2 GiB.
7. Under **Autoscaling**, leave minimum instances at 0 — this is what keeps the chatbot free to run when nobody's using it.
8. Click **Create**.

## Part 7 — Watch it build, then test it

The service starts up as soon as it's created, and usually takes under a minute since the image is already built. When it's ready, click the **URL** near the top of the Cloud Run service page — that's your live, personalized chatbot.

The very first message you send might take a few extra seconds compared to the ones after it — that first request is when the chatbot downloads its knowledge base from the index bucket. Every message after that is fast.

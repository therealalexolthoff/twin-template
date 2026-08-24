# Contributing
 
Thanks for your interest in contributing! This project is a **template**: the goal is for anyone to be able to fork it, personalize `context.py` and `rag_data/`, and deploy their own digital twin on GCP. Because of that, contributions should make the *template* more solid, flexible, or easier to extend — not just work for one person's specific twin.
 
## The shape of the project
 
There are two pipelines, each with its own Dockerfile and Cloud Build trigger:
 
| Pipeline | Entry point | Built by | Runs as |
|---|---|---|---|
| **Ingest** — builds the knowledge base | `ingest.py` | `Dockerfile.ingest` / `cloudbuild-ingest.yaml` | Cloud Run **Job** (`twin-ingest-job`) |
| **Serve** — runs the chatbot | `main.py` | `Dockerfile.serve` / `cloudbuild-serve.yaml` | Cloud Run **Service** (`twin-serve`) |
 
The two pipelines share exactly **one** module: `embed.py`, used by `ingest.py` (embedding documents) and `context.py` (embedding queries). `doc_loader.py` and `chunker.py` are used only by `ingest.py` — the serve side never touches them. When you change `embed.py`, think about **both** sides; a change to `doc_loader.py` or `chunker.py` only affects ingestion.
 
> **Known inconsistency:** `chroma_setup.py`'s `get_collection()` is currently only used by `context.py` (serve side). `ingest.py` builds its own `chromadb.PersistentClient` and calls `get_or_create_collection()` directly instead of importing `chroma_setup`, so the same setup logic exists in two places. Consolidating `ingest.py` to reuse `chroma_setup.get_collection()` would be a good first contribution.
 
## Pipeline map
 
| File | Responsibility | Interface contributors should preserve |
|---|---|---|
| `doc_loader.py` | Load raw documents, from either `DOCS_BUCKET` (GCS) or local `rag_data/` | `prep_docs()` returns a list of `{"text": str, "source": str}` |
| `chunker.py` | Split text into overlapping, topic-respecting chunks | `chunk_text(text, source, ...)` returns a list of chunk dicts with a stable schema (`id`, `source`, `text`, offsets, etc.) — see the module docstring below |
| `embed.py` | Turn text into vectors via Gemini (`gemini-embedding-001` on Vertex AI) | `run_embeddings(input, task_type)` returns a list of vectors |
| `chroma_setup.py` | Get/create the Chroma collection, downloading the index from `INDEX_BUCKET` if it's not already local — **currently used only by `context.py` on the serve side** (see note above) | `get_collection()` returns a Chroma collection supporting `.add()`, `.query()`, `.get()` |
| `ingest.py` | Orchestrates load → chunk → embed → store → upload | `build_and_upload()`; this is what `Dockerfile.ingest` runs |
| `context.py` | Retrieve relevant chunks for a query; hold the persona system prompt | `get_context(query, n_results)` returns a string; `system_prompt()` returns a string |
| `main.py` | Gradio chat UI, wired to Vertex AI's Gemini chat model | This is what `Dockerfile.serve` runs |
 
**`chunker.py` is intentionally the most heavily documented file in the project** — before modifying it, read the design-principles docstring at the top. It explains *why* the function is built the way it is (heading-aware sectioning, pluggable length functions, no cross-section overlap, etc.), and any change should stay consistent with those principles rather than reintroduce a problem they were written to avoid.
 
## The one thing that will break silently: embeddings
 
`embed.py` is called from both `ingest.py` (embedding documents) and `context.py` (embedding a user's query). **Documents and queries have to end up in the same vector space.** If you change the embedding model, `output_dimensionality`, or `task_type` handling in `embed.py`, existing indexes become incompatible with new queries — retrieval won't error, it'll just quietly return bad or empty results. Any PR touching `embed.py` should call this out explicitly and note that a re-run of `ingest.py` is required.
 
## Two Ways To Contribute
 
Everything above is about the **pipeline** — how documents become a searchable index. As of now, the pipeline is stable and reliable. Contributions are welcome, but they will not substantially extend **the value** of the template.

By contrast, **chatbot feature contributions**, modular additions layered on top of `main.py`/`context.py` that change what the twin can *do*, without touching how it retrieves knowledge, can substantially improve the value of the template.

This is new territory for the project, so below is the current state of each area and what a contribution would realistically involve.
 
### Tool calling
 
Vertex AI's Gemini API supports function calling via `types.Tool`/`types.FunctionDeclaration`, passed into `GenerateContentConfig(tools=[...])` — `main.py` doesn't use this yet; `respond_basic()`'s config currently only sets `system_instruction` and `thinking_config`. To keep tools modular, give each one its own file (e.g. `tools/check_calendar.py`) exposing both the function and its schema, and assemble an explicit list of enabled tools before calling `client.chats.create()`, so turning a tool on or off is a one-line change rather than an edit to `respond_basic()` itself. Note that adding tools also means handling the follow-up turn where Gemini returns a function-call part and expects the result sent back — that round trip doesn't exist in `main.py` today and is part of the work, not a detail to skip.
 
### Modular UI features
 
`main.py` currently calls `gr.ChatInterface(fn=respond_basic).launch()` directly, without wrapping it in `gr.Blocks()`. That's the main thing that needs to change — `ChatInterface` itself already has two built-in extension points worth knowing about before reaching for anything more custom:
 
- **`additional_inputs`** — a list of components (sliders, textboxes, dropdowns) rendered in an accordion next to the chat, passed as extra arguments into the chat function. This is the right fit for something like an `n_results` slider or a temperature control — no restructuring needed beyond accepting the extra argument in `respond_basic()`.
- **`additional_outputs`** — components the chat function can also write to, as long as they're declared in the same `gr.Blocks()` scope. This is the mechanism for a "show retrieved sources" panel: declare a `gr.Markdown()`, pass it via `additional_outputs`, and have `respond_basic()` return `(streamed_text, context_string)` instead of just the streamed text.
So most modular UI features should fit inside `gr.Blocks()` + `ChatInterface`'s existing accordion pattern, not a hand-built layout. One thing to avoid: combining `ChatInterface` with `gr.Sidebar()` for a true sidebar layout currently hits a [known Gradio layout bug](https://github.com/gradio-app/gradio/issues/10796) where the two distort each other. Stick to the accordion-based `additional_inputs`/`additional_outputs` pattern unless someone wants to take on that upstream bug as part of the contribution.
 
Because Gradio builds its layout once at startup, "optional" here means *conditionally constructed at launch time from an env var*, not toggled live per user. A minimal version of the pattern:
 
```python
extra_outputs = []
if os.environ.get("ENABLE_SOURCES_PANEL") == "true":
    sources_box = gr.Markdown(label="Sources", render=False)
    extra_outputs.append(sources_box)
 
gr.ChatInterface(fn=respond_basic, additional_outputs=extra_outputs, ...)
```
 
with `respond_basic()` branching on the same flag to decide whether it yields just text or `(text, sources)`. If you're picking up a UI feature, open an issue first to confirm the flag name and on/off convention — the first PR here effectively sets the pattern everyone after you follows.
 
### Multi-modal
 
Concrete gotcha here: `main.py`'s `extract_text()` currently discards any message part that isn't `type == "text"`. If a user uploads an image today, it's silently dropped rather than reaching Gemini — there's no error, the twin just never sees it. Making the twin multimodal means:
- Switching Gradio's chat input to multimodal mode
- Extending (or replacing) `extract_text()` to convert non-text parts into the right Vertex `Part` type (e.g. image bytes) instead of dropping them
- Confirming the configured model (`gemini-3.5-flash-lite`) actually supports whichever modality you're adding — check Vertex AI's current docs rather than assuming, since supported modalities vary by model and change over time
## Local setup
 
This mirrors the "Local Setup" section of `DEPLOYMENT.md`:
 
1. Fork and clone the repo
2. Install [uv](https://docs.astral.sh/uv/) if you don't have it
3. Install the `gcloud` CLI and run `gcloud auth application-default login` once
4. Copy `.env.example` to `.env` and fill in your GCP project ID
5. `uv run ingest.py` — builds a local `chroma_db/` from the `.txt` files in `rag_data/`
6. `uv run main.py` — starts the chatbot locally against that index
If your change only touches `main.py`/`context.py`, you can usually skip re-running `ingest.py` unless you've also changed `embed.py` or `chunker.py`'s output schema.
 
## Adding a new implementation of a pipeline stage
 
If you're adding an alternative — a different vector store, a different embedding provider, a different chunking strategy:
 
- Keep the same function name and return shape described in the pipeline map above, so it's a drop-in replacement
- Note any new environment variables clearly, and add them to `DEPLOYMENT.md`'s variable lists for whichever Cloud Run piece(s) need them (ingest job, serve service, or both)
- If it changes what's stored per chunk (metadata fields, ID format), check `ingest.py` and `context.py` for places that read those fields
If you want to change an existing interface (e.g. what `chunk_text()` returns, or what `get_collection()` needs to support), please open an issue first — it's a shared contract and worth discussing before writing code.
 
## Code style
 
- Follow PEP 8; `black`/`ruff` are welcome but not currently enforced by CI
- Match the documentation density of `chunker.py` for anything non-obvious — a future contributor extending the template should be able to understand *why*, not just *what*
- Keep `main.py`'s inline comments about Vertex AI's `Content`/`Part` types in mind if you're touching the chat logic — that API shape is easy to get subtly wrong
## Testing
 
There's no formal test suite yet — a good first contribution would be adding one, especially around `chunker.py`'s edge cases (no headings, tiny sections, overlap near a section boundary). Until then, the bar is: run `uv run ingest.py` then `uv run main.py` and confirm the pipeline still works end to end for at least one local `.txt` file.
 
## Commit messages
 
```
feat(embed): add support for a local sentence-transformers fallback
fix(chunker): handle empty section after heading merge
docs(deployment): fix broken link to architecture doc
```
 
## Pull requests
 
1. Say which pipeline(s) your change affects — ingest, serve, or both — or, for a chatbot feature (tool calling, UI, multimodal), say whether it's on by default or behind a flag
2. Call out any new/changed environment variables
3. If you touched `embed.py` or `chunker.py`'s output schema, say so explicitly (see the embeddings note above)
4. Small, focused PRs get reviewed fastest
## Questions?
 
Open an issue with the `question` label. If you found the docs unclear enough to need to ask, that's useful signal for a docs fix too.
 
---
 
By contributing, you agree that your contributions will be licensed under the project's [LICENSE](./LICENSE).
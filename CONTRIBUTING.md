# Contributing

Thanks for your interest in contributing! This project is a **template**: the goal is for anyone to be able to fork it, personalize `main/context.py` and `rag_data/`, and deploy their own AI chatbot on GCP. Because of that, contributions should make the *template* more solid, flexible, or easier to extend, not just improve it for one person's specific chatbot.

## The shape of the project

There are two pipelines, each with its own Dockerfile and Cloud Build trigger:

| Pipeline | Entry point | Built by | Runs as |
|---|---|---|---|
| **Ingest** — builds the knowledge base | `run_ingest.py` | `Dockerfile.ingest` / `cloudbuild-ingest.yaml` | Cloud Run **Job** (`twin-ingest-job`) |
| **Serve** — runs the chatbot | `run_app.py` | `Dockerfile.serve` / `cloudbuild-serve.yaml` | Cloud Run **Service** (`twin-serve`) |

The code is split into folders that mirror this:

- `ingest/` — used only by the ingest pipeline (`doc_loader.py`, `chunker.py`)
- `main/` — used only by the serve pipeline (`chat.py`, `context.py`, `load_vector_data.py`, `security.py`)
- `tools/` — the chatbot's callable tools, used only by the serve pipeline
- `shared/` — used by both pipelines

> **Adding dependencies and folders.** Both Dockerfiles install from `pyproject.toml`. A package that both pipelines need goes in `dependencies`; one only the chatbot needs goes in the `serve` dependency group (`uv add --group serve <package>`), which `Dockerfile.serve` installs and `Dockerfile.ingest` skips. Locally, `uv run` installs both. Each Dockerfile also copies only the folders its pipeline uses, so if you add a new top-level folder, add a `COPY` line for it too, or the code will work locally but fail with an `ImportError` on Cloud Run.

The two pipelines share exactly **one** module: `shared/embed.py`, used by `run_ingest.py` (embedding documents) and `main/context.py` (embedding queries). `ingest/doc_loader.py` and `ingest/chunker.py` are used only by `run_ingest.py` — the serve side never touches them. When you change `shared/embed.py`, think about **both** sides; a change to anything in `ingest/` only affects ingestion.

> **Known inconsistency:** `main/load_vector_data.py`'s `get_collection()` is currently only used by `main/context.py` (serve side). `run_ingest.py` builds its own `chromadb.PersistentClient` and calls `get_or_create_collection()` directly instead of importing `load_vector_data`, so the same setup logic exists in two places. Consolidating `run_ingest.py` to reuse `get_collection()` would be a good first contribution.

## Pipeline map

| File | Responsibility | Interface contributors should preserve |
|---|---|---|
| `ingest/doc_loader.py` | Load raw documents, from either `DOCS_BUCKET` (GCS) or local `rag_data/` | `prep_docs()` returns a list of `{"text": str, "source": str}` |
| `ingest/chunker.py` | Split text into overlapping, topic-respecting chunks | `chunk_text(text, source, ...)` returns a list of chunk dicts with a stable schema (`id`, `source`, `text`, offsets, etc.) — see the module docstring. |
| `shared/embed.py` | Turn text into vectors via Gemini (`gemini-embedding-001` on Vertex AI) | `run_embeddings(texts, task_type)` takes a string or list of strings and returns a list of unit-length vectors, one per text |
| `main/load_vector_data.py` | Get/create the Chroma collection, downloading the index from `INDEX_BUCKET` if it's not already local — **currently used only by `main/context.py` on the serve side** (see note above) | `get_collection()` returns a Chroma collection supporting `.add()`, `.query()`, `.get()` |
| `run_ingest.py` | Orchestrates load → chunk → embed → store → upload | `build_and_upload()`; this is what `Dockerfile.ingest` runs |
| `main/context.py` | Retrieve relevant chunks for a query; hold the persona system prompt | `get_context(query, n_results)` returns a string; `system_prompt()` returns a string |
| `main/security.py` | Screen each user prompt with Model Armor before it reaches Gemini | `check_user_prompt(prompt)` returns a rejection message if the prompt is flagged, or `""` if it's clean |
| `main/chat.py` | Chat logic wired to Vertex AI's Gemini chat model, including the tool-calling loop | `respond_basic(message, history)` is the Gradio chat function |
| `tools/tools.py` | Declares the tools Gemini can call and maps them to their Python functions | `tools` (list of `types.Tool`) and `FUNCTION_MAP` (name → function) |
| `run_app.py` | Launches the Gradio chat UI around `respond_basic()` | This is what `Dockerfile.serve` runs |

**`ingest/chunker.py` is intentionally the most heavily documented file in the project** — before modifying it, read the design-principles docstring at the top. It explains *why* the function is built the way it is (heading-aware sectioning, pluggable length functions, no cross-section overlap, etc.), and any change should stay consistent with those principles rather than reintroduce a problem they were written to avoid.

## The one thing that will break silently: embeddings

`shared/embed.py` is called from both `run_ingest.py` (embedding documents) and `main/context.py` (embedding a user's query). **Documents and queries have to end up in the same vector space.** If you change the embedding model, `output_dimensionality`, `task_type` handling, or the normalization in `shared/embed.py` — or the collection's distance setting (cosine) in `run_ingest.py` — existing indexes become incompatible with new queries; retrieval won't error, it'll just quietly return bad or empty results. Any PR touching `shared/embed.py` should call this out explicitly and note that a re-run of `run_ingest.py` is required.

Two more things to know about `shared/embed.py`: `gemini-embedding-001` accepts only **one input per request**, so `run_embeddings` makes one API call per text (a big knowledge base means many calls); and it only returns unit-length vectors at its full 3072 dimensions, so at 256 the vectors are normalized in code before they're stored or queried.

## Two Ways To Contribute

Everything above is about the **pipeline**: how documents become a searchable index. As of now, the pipeline is stable and reliable. Contributions are welcome, but they will not substantially extend **the value** of the template.

By contrast, **chatbot feature contributions**, modular additions layered on top of `main/chat.py`/`main/context.py` that change what the chatbot can *do*, without touching how it retrieves knowledge, can substantially improve the value of the template.

This is new territory for the project, so below is the current state of each area and what a contribution would realistically involve.

### Tool calling

Tool calling is implemented. Each tool lives in its own file in `tools/` (e.g. `tools/dice_roll.py`, `tools/notify.py`), and `tools/tools.py` declares each one's schema as a `types.FunctionDeclaration`, collects them into the `tools` list passed to `GenerateContentConfig(tools=[...])`, and maps each tool name to its Python function in `FUNCTION_MAP`. `respond_basic()` in `main/chat.py` handles the round trip: when Gemini returns function calls, it runs them via `FUNCTION_MAP`, sends the results back, and repeats for up to `MAX_TOOL_ROUNDS` rounds.

To add a tool:

1. Create `tools/<your_tool>.py` with the function. Return a string the model can read, and avoid raising — return an error message instead (see `tools/notify.py`).
2. In `tools/tools.py`, add a `FunctionDeclaration` with a clear description of *when* the model should use it, add it to the `function_declarations` list, and add it to `FUNCTION_MAP`.
3. Document any new environment variables (see "Adding a new implementation of a pipeline stage" below).

Turning a tool off is a matter of removing it from those two lists — `respond_basic()` itself shouldn't need to change.

### Modular UI features

`run_app.py` currently calls `gr.ChatInterface(fn=respond_basic).launch()` directly, without wrapping it in `gr.Blocks()`. That's the main thing that needs to change: `ChatInterface` itself already has two built-in extension points worth knowing about before reaching for anything more custom:

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

Concrete gotcha here: `extract_text()` in `main/chat.py` currently discards any message part that isn't `type == "text"`. If a user uploads an image today, it's silently dropped rather than reaching Gemini — there's no error, the chatbot just never sees it. Making the chatbot multimodal means:

- Switching Gradio's chat input to multimodal mode
- Extending (or replacing) `extract_text()` to convert non-text parts into the right Vertex `Part` type (e.g. image bytes) instead of dropping them
- Confirming the configured model (`gemini-3.5-flash-lite`) actually supports whichever modality you're adding — check Vertex AI's current docs rather than assuming, since supported modalities vary by model and change over time

## Local setup

This mirrors the "Local Setup" section of [`GCP_DEPLOYMENT.md`](./GCP_DEPLOYMENT.md):

1. Fork and clone the repo
2. Install [uv](https://docs.astral.sh/uv/) if you don't have it
3. Install the `gcloud` CLI and run `gcloud auth application-default login` once
4. Create a `.env` file in the repo root containing `PROJECT_ID=your-project-id`
5. `uv run run_ingest.py` — builds a local `chroma_db/` from the `.txt` files in `rag_data/`
6. `uv run run_app.py` — starts the chatbot locally against that index

If your change only touches `main/` or `tools/`, you can usually skip re-running `run_ingest.py` unless you've also changed `shared/embed.py` or `ingest/chunker.py`'s output schema.

## Adding a new implementation of a pipeline stage

If you're adding an alternative — a different vector store, a different embedding provider, a different chunking strategy:

- Keep the same function name and return shape described in the pipeline map above, so it's a drop-in replacement
- Note any new environment variables clearly, and add them to `GCP_DEPLOYMENT.md`'s variable lists for whichever Cloud Run piece(s) need them (ingest job, serve service, or both)
- If it changes what's stored per chunk (metadata fields, ID format), check `run_ingest.py` and `main/context.py` for places that read those fields

If you want to change an existing interface (e.g. what `chunk_text()` returns, or what `get_collection()` needs to support), please open an issue first — it's a shared contract and worth discussing before writing code.

## Code style

- Follow PEP 8; `black`/`ruff` are welcome but not currently enforced by CI
- Match the documentation density of `ingest/chunker.py` for anything non-obvious — a future contributor extending the template should be able to understand *why*, not just *what*
- Keep `main/chat.py`'s inline comments about Vertex AI's `Content`/`Part` types in mind if you're touching the chat logic — that API shape is easy to get subtly wrong

## Testing

There's no formal test suite yet — a good first contribution would be adding one, especially around `ingest/chunker.py`'s edge cases (no headings, tiny sections, overlap near a section boundary). Until then, the bar is: run `uv run run_ingest.py` then `uv run run_app.py` and confirm the pipeline still works end to end for at least one local `.txt` file.

## Commit messages

```
feat(embed): add support for a local sentence-transformers fallback
fix(chunker): handle empty section after heading merge
docs(deployment): fix broken link to architecture doc
```

## Pull requests

1. Say which pipeline(s) your change affects — ingest, serve, or both — or, for a chatbot feature (tool calling, UI, multimodal), say whether it's on by default or behind a flag
2. Call out any new/changed environment variables
3. If you touched `shared/embed.py` or `ingest/chunker.py`'s output schema, say so explicitly (see the embeddings note above)
4. Small, focused PRs get reviewed fastest

## Questions?

Open an issue with the `question` label. If you found the docs unclear enough to need to ask, that's useful signal for a docs fix too.

---

By contributing, you agree that your contributions will be licensed under the project's [LICENSE](./LICENSE).

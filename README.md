# Infographix

Infographix is a FastAPI-powered reference application that orchestrates Google Gemini native image-generation models to create modular, revision-friendly infographics. Users can choose models, presets, styles, text handling options, and rendering workflows (pure image or hybrid text overlay) through both REST APIs and an HTMX-driven UI.

## Key Features
- **Model-aware planning** with low-latency (`models/gemini-2.5-flash-image`) and premium (`models/gemini-3.1-flash-image-preview`) modes plus easy extension to future variants.
- **Structured planner** converts raw user input into `InfographicSpec` objects with text budgets, rendering mode recommendations, and warnings.
- **Modular prompt composer** stitches prompt fragments from style presets, infographic presets, palette data, and text-handling guidance.
- **Swappable rendering backend** via `GeminiImageClient`, including placeholder rendering when no API key is configured.
- **Hybrid overlay pipeline** uses Pillow to render deterministic text on top of Gemini imagery when exact typography is required.
- **SQLite persistence** for raw requests, normalized specs, prompts, assets, warnings, and revision chains.
- **HTMX + Jinja UI** for spec previews, generation, revision, and history browsing.
- **Image Generation Chat + meta prompting** to iteratively design Infographix-ready JSON prompts, reverse engineer existing images, and paste structured output back into the builder.

## Project Structure
```
app/
  config.py              # Pydantic settings + env handling
  main.py                # FastAPI factory, middleware, routers
  db.py                  # Async SQLAlchemy models + session helpers
  models/                # Pydantic specs + preset schemas
  routers/               # API + UI routers
  services/              # Planner, composer, Gemini client, overlay, etc.
presets/
  styles/*.yaml          # Style presets
  infographics/*.yaml    # Infographic-type presets
app/templates/, app/static/  # UI assets
storage/                 # Generated outputs + reference uploads
```

## Requirements
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for dependency and venv management
- Google API key for Gemini image models (optional, placeholder rendering without it)

## Getting Started
1. **Install dependencies**
   ```bash
   uv sync
   ```
2. **Activate the environment** (if necessary)
   ```bash
   source .venv/bin/activate  # or `uv venv && source .venv/bin/activate`
   ```
3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # edit GOOGLE_API_KEY and DATABASE_URL as needed
   ```
4. **Run the dev server**
   ```bash
   uv run fastapi dev app/main.py  # or uv run uvicorn app.main:app --reload
   ```
   Visit `http://localhost:8000/` for the UI or `/docs` for the API.

## Using the Web UI
1. **Open the app** – Navigate to `http://localhost:8000/` after the dev server starts.
2. **Enter basics** – Provide a topic and (optionally) the target audience in the first text fields.
3. **Pick model + presets** – Choose the Gemini model, infographic type, and visual style from the dropdowns. These map directly to the preset YAMLs in `presets/`.
4. **Leverage Meta Prompt paste** (optional) – A new “Paste Meta Prompt” panel lets you drop the JSON emitted by Image Generation Chat (Meta Prompt mode). Click **Apply Meta Prompt** and the form auto-fills topic, presets, aspect/size, text flags, and section cards. The status line will remind you to upload any reference assets noted in the JSON.
5. **Add text & layout guidance** – Fine-tune title/subtitle/footer, aspect ratio, output size, and adjust section cards using the builder. Toggle exact-text or rendering-mode preferences if needed.
6. **Upload references (optional)** – Attach any reference images; they’ll be validated and stored for the run.
7. **Preview the spec** – Click **Preview Spec** to POST to `/preview` via HTMX. The panel on the right shows the normalized `InfographicSpec`, text-budget warnings, and any planner recommendations before you spend tokens.
8. **Generate** – When satisfied, hit **Generate**. The server will compose the prompt, call Gemini (or the placeholder renderer), persist the run, and redirect you to a detail page with the image, prompt, warnings, and structured spec.
9. **Review history** – Use the top navigation’s “History” link to browse prior generations; each row links to the full detail view for revisions or downloads.

## Image Generation Chat & Meta Prompting
The chat studio (nav: “Image Generation Chat”) now mirrors modern AI chat UX:

1. **Modes** – Chips for Auto, Chat, Imagine, and **Meta Prompt** control the response type. Auto still auto-detects via heuristics + classifier; Meta Prompt explicitly gathers structured Infographix context.
2. **Markdown rendering** – Gemini replies render as markdown with code fences, lists, and inline code for copy-ready prompts.
3. **Meta Prompt workflow**:
   - Switch to *Meta Prompt* mode.
   - Describe the existing image or goal; upload optional references.
   - Gemini asks follow-up questions until enough detail exists.
   - Final replies include `META PROMPT READY` plus a ```json … ``` block containing Infographix fields (topic, presets, sections, etc.).
   - Copy that JSON and paste it into the builder’s Meta Prompt panel to auto-fill the form.
4. **Attachments** – Text uploads become inline snippets; binaries become base64 inline data, so Gemini can “see” the provided context.
5. **Downloads & iterations** – Image responses include download links and iteration buttons. Meta Prompt replies show a badge and can be copied wholesale.

## Tooling
- **Linting:** `uv run ruff check .`
- **Type checking:** `uv run mypy app`
- **Testing:** `uv run pytest`

## API Overview
- `GET /api/models` – list supported Gemini model capabilities.
- `GET /api/styles` / `GET /api/infographics` – enumerate presets.
- `POST /api/spec/preview` – normalize user input into an `InfographicSpec`.
- `POST /api/render` – run full pipeline, persist generation, and return result metadata.
- `POST /api/revise/{id}` – apply revision overrides and render a new version.
- `GET /api/history` – list past generations.
- `GET /api/history/{id}` – retrieve a single generation record.

All API endpoints accept/return JSON compatible with the Pydantic schemas in `app/models/specs.py`.

## Testing
The pytest suite covers preset loading, planner heuristics, prompt composition, text-budget logic, and key API routes. Run the entire suite with:
```bash
uv run pytest
```

## Notes
- When no `GOOGLE_API_KEY` is configured, the app produces placeholder images with the composed prompt text for local testing.
- Reference images are validated and stored under `storage/reference/`; generated outputs are written to `storage/outputs/` and served via `/storage/...` URLs.

# Infographix Agents Overview

This document explains the “agents” that cooperate inside the Infographix application. Each agent is a focused service with a clearly defined contract—inputs, outputs, and responsibilities—so that planning, prompt composition, rendering, chat, and persistence remain modular.

---

## 1. Core Pipelines

### 1.1 Infographic Generation Flow
1. **UserInput capture (UI / API)** – topic, audience, preset selections, text preferences, aspect & size controls, render mode hints, reference uploads.
2. **Infographic Planner** (`app/services/planner.py`) – normalizes the request into an `InfographicSpec`. It:
   - Selects/recommends models (`gemini-2.5-flash-image` for low-latency vs `gemini-3.1-flash-image-preview` for fidelity, with future-proofing for `gemini-3-pro-image-preview`).
   - Chooses layout guidance, composition density, estimated text budgets, warnings (text-heavy, summarization needs), and rendering mode (`pure_image` vs `hybrid_overlay`).
   - Determines whether exact text rendering or overlay is required and flags hybrid overlay when the request is dense.
3. **Prompt Composer** (`app/services/prompt_composer.py`) – takes the `InfographicSpec` and builds a modular prompt:
   - Layers: global constraints, model-specific rules, style preset fragments, infographic-type layout instructions, palette/branding, text budget directives, section-level instructions, negative constraints.
   - Ensures prompt isn’t a single block string but composed from fragments that can be swapped per preset.
4. **Gemini Image Renderer** (`app/services/gemini_client.py`) – calls the selected image model with the composed prompt. Handles aspect ratio & size normalization, saves binary outputs to `storage/outputs`, and returns an `ImageRenderResult`.
5. **Text Overlay Renderer** (`app/services/text_overlay.py`) – optional hybrid overlay stage for deterministic text (title, subtitle, key labels) drawn with Pillow when planner opts for `hybrid_overlay`.
6. **History Store** (`app/services/history_store.py`) – persists user input, normalized spec, prompt, model, render mode, warnings, reference metadata, and saved output path. Provides APIs for listing and retrieving revisions.

### 1.2 Chat / Image Studio Flow
1. **Chat Store** (`app/services/chat_store.py`) – async persistence layer for chat sessions, messages, attachments, and iteration metadata.
2. **Gemini Text Client** (`app/services/text_client.py`) – handles multimodal chat replies. It now supports:
   - Streaming-compatible payloads (`parts`) so attachments become inline context.
   - `detect_response_mode`, which first uses heuristics then a lightweight call to `chat_router_model` (`models/gemini-2.0-flash`) to decide between text or image responses when users leave “Auto” selected.
3. **Gemini Image Client** – reused by chat when the resolved mode is `image`. Iterations reuse the parent prompt chain.
4. **Chat Attachments Agent** (`app/services/chat_attachments.py`) – validates uploads (≤5 MB), stores them under `storage/chat_uploads`, and converts them to either inline text snippets (for textual files) or base64 inline data parts for multimodal chat.
5. **UI State Agent** (`app/static/js/htmx_helpers.js`) – mode detection, auto model-switching, attachments preview, zoomed image viewing, section builder logic for Infographix, etc.

---

## 2. Agent Catalog

| Agent | Location | Inputs | Outputs | Notes |
| --- | --- | --- | --- | --- |
| **Infographic Planner** | `app/services/planner.py` | `UserInput` + presets | `InfographicSpec` | Normalizes data, enforces text budgets, sets warnings, selects recommended model & rendering mode. |
| **Prompt Composer** | `app/services/prompt_composer.py` | `InfographicSpec` + presets | Structured prompt string | Pulls preset YAML fragments (styles + infographic types). |
| **Gemini Image Client** | `app/services/gemini_client.py` | Prompt + model + size + aspect | `ImageRenderResult` (path + prompt + model) | Supports `gemini-2.5-flash-image` & `gemini-3.1-flash-image-preview`. Future model IDs can be added without refactoring. |
| **Text Overlay Renderer** | `app/services/text_overlay.py` | Pillow image + overlay instructions | PNG with deterministic text | Only used when planner sets `hybrid_overlay`. |
| **History Store** | `app/services/history_store.py` | Generation metadata | Query interface for history UI/API | Links generation IDs to specs & prompts. |
| **Chat Store** | `app/services/chat_store.py` | Session & message data | ORM accessors | Keeps per-session message chains with parent pointers for image iteration. |
| **Gemini Text Client** | `app/services/text_client.py` | Chat payload | Reply text | Handles attachments via `parts`, includes auto-routing (`detect_response_mode`). |
| **Gemini Image Client (chat)** | Same as infographic renderer | Prompt + model | Image message saved to `storage/outputs` | Shared code path ensures consistent formatting. |
| **Chat Router** | `text_client.detect_response_mode` + heuristics | Prompt text + attachments | Mode decision (`text` / `image`) | Uses heuristics first, then `chat_router_model` to classify ambiguous prompts. Sticky manual modes override. |
| **Chat Attachments Agent** | `app/services/chat_attachments.py` | `UploadFile` array | Stored files + inline prompt parts | Produces metadata for UI and input for text client. |
| **Reference Image Service** | `app/services/reference_images.py` | Infographix reference uploads | `ReferenceImageSpec` list | Validates counts, roles, file sizes, aspect hints. |
| **Section Builder (UI agent)** | `app/static/js/htmx_helpers.js` | DOM templates + user input | JSON stored in hidden field | Generates normalized structure for `sections_json`. |

---

## 3. Key Data Shapes

### 3.1 `UserInput`
- Topic, audience dropdown, desired model, infographic type, visual style.
- Title / subtitle / footer.
- Aspect ratio + image size controls (`Auto`, preset-based defaults, or custom text inputs).
- Rendering mode preference, exact text flag, text preference.
- Sections array (built by the HTMX section builder).
- Reference images (converted to `ReferenceImageSpec`).

### 3.2 `InfographicSpec`
- IDs: request_id, selected_model, recommended_model.
- Layout: infographic_type, visual_style, composition_density, layout guidance.
- Copy plan: title, subtitle, sections (with `InfographicSection` + `TextBlock`), footer, palette, background style.
- Text strategy: `exact_text_required`, `text_can_be_summarized`, `text_budget_status`, warnings.
- Rendering params: aspect_ratio, image_size, rendering_mode, overlay instructions, reference images metadata.
- Revision data: revision_notes, warnings, metadata for UI.

### 3.3 Chat Messages (`ChatMessage`)
- `message_type`: `text` or `image`.
- `content`, `prompt`, `image_path`, `parent_message_id`.
- `extra.attachments`: list of stored attachment metadata (path, original name, size, content type). UI maps those to download pills.

---

## 4. Model Strategy

| Model | Purpose | Notes |
| --- | --- | --- |
| `gemini-2.5-flash-image` | Fast / low-latency rendering; default Image Generation Chat recommendation when requests are light or near real-time. | Encouraged for quick iteration; planner flags text-heavy requests to avoid this model when necessary. |
| `gemini-3.1-flash-image-preview` | Higher fidelity, more aspect ratios, better typography, supports up to 14 references. | Planner upgrades to this model when exact text matters or when resolution/aspect requirements exceed Flash capabilities. |
| `gemini-2.5-pro` (text) | Chat default for conversational replies. | Configured in `CHAT_TEXT_MODELS`. |
| `chat_router_model` (`models/gemini-2.0-flash`) | Lightweight classifier for automatic text vs image detection in the chat composer. | The route only runs when heuristics are inconclusive and user hasn’t manually forced a mode. |

Future models (e.g., `gemini-3-pro-image-preview`) can plug into `CHAT_IMAGE_MODELS` and planner capability maps without rewriting the pipeline.

---

## 5. Rendering Modes
- **`pure_image`** – Entire output (art + typography) via Gemini.
- **`hybrid_overlay`** – Gemini renders composition; Pillow overlays exact titles/labels. Planner shifts to this automatically for dense, exact text requests but can be user-overridden.

---

## 6. Attachment Handling (Chat)
- Saved under `storage/chat_uploads/<uuid>_<sanitized_name>`.
- Validation: non-empty, ≤5 MB (`settings.max_upload_bytes`), MIME detection stored.
- Text-like files (plain text, CSV, JSON, Markdown, XML) become inline text parts with truncation + header, so short documents become context for Gemini chat.
- Binary files (images, other data) are base64 encoded into `inline_data` parts for the Gemini SDK.
- UI preview chips show filename + size; downloads served through `/storage/...` if the file sits inside the configured storage root.

---

## 7. Persistence Agents
- **SQLite via SQLAlchemy** – `chat_sessions`, `chat_messages`, `generations`.
- All writes go through async sessions; `ChatStore` updates `updated_at` timestamps automatically.
- History endpoints use `HistoryStore` to fetch generation lists, detail pages, and revision chains.

---

## 8. Extension Points
- **New Model Capability Matrices** – plug into `app/services/model_capabilities.py` to specify allowed aspect ratios, max sizes, text density guidance.
- **Additional Agents** – e.g., “reference image classifier,” “prompt critique agent,” or “analytics agent” can hook in by reading/writing to the existing data structures.
- **Streaming Chat** – `GeminiTextClient` already builds `contents` arrays that are compatible with SSE streaming; future work can expose WebSocket endpoints.
- **Image Editing Iterations** – current iteration button simply reuses parent prompt; future “blend/edit” agent could attach image bytes and textual instructions before calling Gemini Vision or Imagen editing APIs.

---

## 9. Operational Notes
- Env management with `uv`; dependencies defined in `pyproject.toml`.
- `.env` holds `GOOGLE_API_KEY`. Without it, Gemini clients raise runtime errors.
- Static assets (CSS/JS) mimic the Image Generation Chat visual language across Infographix, History, and Chat pages for continuity.
- Tests (`tests/test_chat_utils.py`, planner/preset/prompt suites) ensure spec normalization, prompt modularity, model validation, and text budget logic remain stable.

---

Keeping this overview accurate makes it easier to reason about how new features (e.g., “Studio Chat” improvements, preset templates, advanced overlay workflows) fit into the agent mesh without introducing monolith-style coupling. Update the relevant section whenever you add a service or change a pipeline boundary.***

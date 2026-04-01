from __future__ import annotations

import json
import uuid
from pathlib import Path
from dataclasses import asdict
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models.presets import PresetRepository
from app.models.specs import InfographicSection, InfographicSpec, ReferenceImageRole, RenderingMode, UserInput
from app.models.chat import ChatResponseMode
from app.services.chat_store import ChatStore
from app.services.history_store import HistoryStore
from app.services.planner import InfographicPlanner
from app.services.prompt_composer import PromptComposer
from app.services.reference_images import store_reference_image
from app.services.text_overlay import apply_overlay
from app.services.gemini_client import GeminiImageClient
from app.services.text_client import GeminiTextClient
from app.services.chat_attachments import save_chat_attachment, attachment_to_part, summarize_attachments
from app.data.test_prompts import TEST_PROMPTS

router = APIRouter(tags=["ui"])
settings = get_settings()
CHAT_TEXT_MODELS = [
    {"id": "models/gemini-2.5-pro", "label": "Gemini 2.5 Pro (text/chat)"},
]
CHAT_IMAGE_MODELS = [
    {"id": "models/gemini-2.5-flash-image", "label": "Gemini 2.5 Flash Image (fast)"},
    {"id": "models/gemini-3.1-flash-image-preview", "label": "Gemini 3.1 Flash Image Preview (fidelity)"},
]
CHAT_TEXT_MODEL_IDS = {model["id"] for model in CHAT_TEXT_MODELS}
CHAT_IMAGE_MODEL_IDS = {model["id"] for model in CHAT_IMAGE_MODELS}
DEFAULT_CHAT_TITLE = "Image Generation Chat"
CHAT_SUGGESTIONS = [
    "Create a keynote-ready infographic about climate resilience",
    "Summarize this data story in three beats with a hero visual",
    "Draft a technical explainer for our model architecture diagram",
]


def get_templates(request: Request):
    return request.app.state.templates


def get_presets(request: Request) -> PresetRepository:
    return request.app.state.preset_repo


def get_planner(request: Request) -> InfographicPlanner:
    return request.app.state.planner


def get_composer(request: Request) -> PromptComposer:
    return request.app.state.prompt_composer


def get_gemini(request: Request) -> GeminiImageClient:
    return request.app.state.gemini_client


def get_text_client(request: Request) -> GeminiTextClient:
    return request.app.state.gemini_text_client


async def get_chat_store(session: AsyncSession = Depends(get_session)) -> ChatStore:
    return ChatStore(session)


async def get_history_store(session: AsyncSession = Depends(get_session)) -> HistoryStore:
    return HistoryStore(session)


def _public_path(path: str | None) -> str | None:
    if not path:
        return None
    absolute = Path(path)
    try:
        relative = absolute.resolve().relative_to(settings.storage_path.resolve())
        return f"/storage/{relative.as_posix()}"
    except ValueError:
        return path


def _parse_sections(payload: str) -> List[InfographicSection]:
    if not payload:
        return []
    data = json.loads(payload)
    return [InfographicSection(**item) for item in data]


async def _build_user_input(
    request_id: str,
    topic: str,
    audience: str | None,
    desired_model: str,
    infographic_type: str,
    visual_style: str,
    sections_json: str,
    title: str | None,
    subtitle: str | None,
    footer_text: str | None,
    aspect_ratio: str | None,
    image_size: str | None,
    exact_text_required: bool,
    text_preference: str | None,
    render_mode: str | None,
    reference_uploads: List[UploadFile] | None,
) -> UserInput:
    try:
        sections = _parse_sections(sections_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid sections JSON: {exc}") from exc
    references = []
    for upload in reference_uploads or []:
        if upload and upload.filename:
            references.append(await store_reference_image(upload, ReferenceImageRole.STYLE))

    mode = None
    if render_mode:
        try:
            mode = RenderingMode(render_mode)
        except ValueError:
            mode = None
    return UserInput(
        request_id=request_id,
        topic=topic,
        audience=audience,
        desired_model=desired_model,
        infographic_type=infographic_type,
        visual_style=visual_style,
        title=title,
        subtitle=subtitle,
        sections=sections,
        footer_text=footer_text,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        exact_text_required=exact_text_required,
        text_preference=text_preference,
        reference_images=references,
        render_mode=mode,
    )


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    presets: PresetRepository = Depends(get_presets),
):
    templates = get_templates(request)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "styles": presets.list_styles(),
            "infographics": presets.list_infographics(),
            "section_templates": [preset.model_dump() for preset in presets.list_section_templates()],
            "test_prompts": TEST_PROMPTS,
        },
    )


@router.get("/chat", response_class=HTMLResponse)
async def chat_home(
    request: Request,
    session_id: str | None = None,
    chat_store: ChatStore = Depends(get_chat_store),
):
    session = await _get_or_create_chat_session(chat_store, session_id)
    templates = get_templates(request)
    context = await _build_chat_context(request, chat_store, session)
    return templates.TemplateResponse(request, "chat.html", context)


@router.post("/chat/session", response_class=HTMLResponse)
async def create_chat_session_ui(
    request: Request,
    title: str = Form(default=None),
    chat_store: ChatStore = Depends(get_chat_store),
):
    clean_title = (title or "").strip() or DEFAULT_CHAT_TITLE
    record = await chat_store.create_session(clean_title, CHAT_TEXT_MODELS[0]["id"])
    return RedirectResponse(f"/chat?session_id={record.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/chat/{session_id}/delete", response_class=HTMLResponse)
async def delete_chat_session(
    session_id: str,
    chat_store: ChatStore = Depends(get_chat_store),
):
    await chat_store.delete_session(session_id)
    return RedirectResponse("/chat", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/chat/{session_id}/send", response_class=HTMLResponse)
async def send_chat_message(
    session_id: str,
    request: Request,
    content: str = Form(...),
    response_mode: str = Form(default=ChatResponseMode.AUTO.value),
    model_id: str = Form(...),
    parent_message_id: str | None = Form(default=None),
    attachments: List[UploadFile] | None = File(default=None),
    chat_store: ChatStore = Depends(get_chat_store),
    text_client: GeminiTextClient = Depends(get_text_client),
    gemini: GeminiImageClient = Depends(get_gemini),
):
    stripped = content.strip()
    if not stripped:
        return RedirectResponse(f"/chat?session_id={session_id}", status_code=status.HTTP_303_SEE_OTHER)

    session = await chat_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    stored_attachments: list[dict] = []
    for upload in attachments or []:
        if upload and upload.filename:
            try:
                saved = await save_chat_attachment(upload)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            if saved:
                stored_attachments.append(asdict(saved))

    try:
        requested_mode = ChatResponseMode(response_mode)
    except ValueError:
        requested_mode = ChatResponseMode.AUTO

    user_message = await chat_store.add_message(
        session_id,
        role="user",
        message_type=(requested_mode if requested_mode != ChatResponseMode.AUTO else ChatResponseMode.TEXT).value,
        content=stripped,
        model=model_id,
        parent_message_id=parent_message_id,
        extra={"attachments": stored_attachments} if stored_attachments else None,
    )

    parent_message = await chat_store.get_message(parent_message_id) if parent_message_id else None

    if requested_mode == ChatResponseMode.META_PROMPT:
        resolved_mode = ChatResponseMode.META_PROMPT
    elif parent_message and parent_message.message_type == ChatResponseMode.IMAGE.value:
        resolved_mode = ChatResponseMode.IMAGE
    elif requested_mode == ChatResponseMode.AUTO:
        resolved_mode = await text_client.detect_response_mode(stripped, stored_attachments)
    else:
        resolved_mode = requested_mode

    try:
        if resolved_mode == ChatResponseMode.IMAGE and model_id not in CHAT_IMAGE_MODEL_IDS:
            model_id = CHAT_IMAGE_MODELS[0]["id"]
        if resolved_mode == ChatResponseMode.TEXT and model_id not in CHAT_TEXT_MODEL_IDS:
            model_id = CHAT_TEXT_MODELS[0]["id"]

        if resolved_mode in (ChatResponseMode.TEXT, ChatResponseMode.META_PROMPT):
            history = await chat_store.list_messages(session_id, limit=50)
            payload = _build_model_payload(history[-20:])
            if resolved_mode == ChatResponseMode.META_PROMPT:
                reply = await text_client.generate_meta_prompt(model_id, payload)
            else:
                reply = await text_client.generate_reply(model_id, payload)
            await chat_store.add_message(
                session_id,
                role="assistant",
                message_type=resolved_mode.value,
                content=reply or "(no response)",
                model=model_id,
            )
        else:
            prompt = _build_chat_image_prompt(stripped, parent_message)
            result = await gemini.generate_image(
                prompt=prompt,
                model=model_id,
                size="1920x1080",
                aspect_ratio="16:9",
            )
            await chat_store.add_message(
                session_id,
                role="assistant",
                message_type=ChatResponseMode.IMAGE.value,
                content="Generated image",
                model=model_id,
                prompt=prompt,
                image_path=result.image_path,
                parent_message_id=parent_message_id or user_message.id,
            )
    except RuntimeError as exc:
        templates = get_templates(request)
        context = await _build_chat_context(request, chat_store, session, error_message=str(exc))
        return templates.TemplateResponse(request, "chat.html", context, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    return RedirectResponse(f"/chat?session_id={session_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/preview", response_class=HTMLResponse)
async def preview_spec(
    request: Request,
    topic: str = Form(...),
    audience: str | None = Form(default=None),
    desired_model: str = Form(default="models/gemini-2.5-flash-image"),
    infographic_type: str = Form(...),
    visual_style: str = Form(...),
    sections_json: str = Form("[]"),
    title: str | None = Form(default=None),
    subtitle: str | None = Form(default=None),
    footer_text: str | None = Form(default=None),
    aspect_ratio: str | None = Form(default=None),
    image_size: str | None = Form(default=None),
    exact_text_required: bool = Form(default=False),
    text_preference: str | None = Form(default="summarize"),
    render_mode: str | None = Form(default=None),
    reference_images: List[UploadFile] | None = File(default=None),
    planner: InfographicPlanner = Depends(get_planner),
):
    user_input = await _build_user_input(
        request_id=str(uuid.uuid4()),
        topic=topic,
        audience=audience,
        desired_model=desired_model,
        infographic_type=infographic_type,
        visual_style=visual_style,
        sections_json=sections_json,
        title=title,
        subtitle=subtitle,
        footer_text=footer_text,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        exact_text_required=exact_text_required,
        text_preference=text_preference,
        render_mode=render_mode,
        reference_uploads=reference_images or [],
    )
    spec = planner.plan(user_input)
    templates = get_templates(request)
    return templates.TemplateResponse(request, "spec_preview.html", {"spec": spec})


@router.post("/generate", response_class=HTMLResponse)
async def generate_ui(
    request: Request,
    topic: str = Form(...),
    audience: str | None = Form(default=None),
    desired_model: str = Form(default="models/gemini-2.5-flash-image"),
    infographic_type: str = Form(...),
    visual_style: str = Form(...),
    sections_json: str = Form("[]"),
    title: str | None = Form(default=None),
    subtitle: str | None = Form(default=None),
    footer_text: str | None = Form(default=None),
    aspect_ratio: str | None = Form(default=None),
    image_size: str | None = Form(default=None),
    exact_text_required: bool = Form(default=False),
    text_preference: str | None = Form(default="summarize"),
    render_mode: str | None = Form(default=None),
    reference_images: List[UploadFile] | None = File(default=None),
    planner: InfographicPlanner = Depends(get_planner),
    composer: PromptComposer = Depends(get_composer),
    gemini: GeminiImageClient = Depends(get_gemini),
    history: HistoryStore = Depends(get_history_store),
):
    request_id = str(uuid.uuid4())
    user_input = await _build_user_input(
        request_id=request_id,
        topic=topic,
        audience=audience,
        desired_model=desired_model,
        infographic_type=infographic_type,
        visual_style=visual_style,
        sections_json=sections_json,
        title=title,
        subtitle=subtitle,
        footer_text=footer_text,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        exact_text_required=exact_text_required,
        text_preference=text_preference,
        render_mode=render_mode,
        reference_uploads=reference_images or [],
    )
    spec = planner.plan(user_input)
    prompt = composer.compose(spec)
    try:
        result = await gemini.generate_image(
            prompt=prompt,
            model=spec.selected_model,
            size=spec.image_size,
            aspect_ratio=spec.aspect_ratio,
            reference_images=spec.reference_images,
        )
    except RuntimeError as exc:
        templates = get_templates(request)
        return templates.TemplateResponse(
            request,
            "detail.html",
            {
                "spec": spec,
                "prompt": prompt,
                "image_path": None,
                "warnings": spec.warnings,
                "error_message": str(exc),
            },
            status_code=503,
        )

    image_path = result.image_path
    if spec.rendering_mode.value == "hybrid_overlay":
        image_path = apply_overlay(image_path, spec)
    generation_id = await history.save_generation(
        spec=spec,
        prompt=prompt,
        selected_model=spec.selected_model,
        rendering_mode=spec.rendering_mode.value,
        user_input=user_input.model_dump(mode="json"),
        warnings=spec.warnings,
        image_path=image_path,
        reference_images=[ri.model_dump() for ri in spec.reference_images],
        revision_notes=user_input.revision_notes,
        parent_id=user_input.revision_of,
    )

    return RedirectResponse(f"/history/{generation_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/history", response_class=HTMLResponse)
async def history_view(request: Request, history: HistoryStore = Depends(get_history_store)):
    records = await history.list_generations(limit=50)
    templates = get_templates(request)
    return templates.TemplateResponse(
        request,
        "history.html",
        {"records": records},
    )


@router.get("/history/{generation_id}", response_class=HTMLResponse)
async def history_detail(
    generation_id: str,
    request: Request,
    history: HistoryStore = Depends(get_history_store),
):
    record = await history.get_generation(generation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Generation not found")
    templates = get_templates(request)
    context = await _build_history_detail_context(request, history, record, error_message=None)
    return templates.TemplateResponse(request, "detail.html", context)


@router.post("/history/{generation_id}/revise", response_class=HTMLResponse)
async def history_revise(
    generation_id: str,
    request: Request,
    message: str = Form(...),
    history: HistoryStore = Depends(get_history_store),
    planner: InfographicPlanner = Depends(get_planner),
    composer: PromptComposer = Depends(get_composer),
    gemini: GeminiImageClient = Depends(get_gemini),
):
    record = await history.get_generation(generation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Generation not found")
    instructions = (message or "").strip()
    if not instructions:
        return RedirectResponse(f"/history/{generation_id}", status_code=status.HTTP_303_SEE_OTHER)
    try:
        user_input = UserInput(**record.user_input)
    except Exception as exc:  # pragma: no cover - corrupted history entry
        raise HTTPException(status_code=500, detail=f"Unable to load base request: {exc}") from exc

    combined_notes = instructions
    if user_input.revision_notes:
        combined_notes = f"{user_input.revision_notes}\n\nAdditional request:\n{instructions}"

    user_input.revision_notes = combined_notes
    user_input.revision_of = generation_id
    user_input.request_id = str(uuid.uuid4())

    spec = planner.plan(user_input)
    prompt = composer.compose(spec)

    try:
        result = await gemini.generate_image(
            prompt=prompt,
            model=spec.selected_model,
            size=spec.image_size,
            aspect_ratio=spec.aspect_ratio,
            reference_images=spec.reference_images,
        )
    except RuntimeError as exc:
        templates = get_templates(request)
        context = await _build_history_detail_context(request, history, record, error_message=str(exc))
        return templates.TemplateResponse(request, "detail.html", context, status_code=503)

    image_path = result.image_path
    if spec.rendering_mode.value == "hybrid_overlay":
        image_path = apply_overlay(image_path, spec)

    child_id = await history.save_generation(
        spec=spec,
        prompt=prompt,
        selected_model=spec.selected_model,
        rendering_mode=spec.rendering_mode.value,
        user_input=user_input.model_dump(mode="json"),
        warnings=spec.warnings,
        image_path=image_path,
        reference_images=[ri.model_dump() for ri in spec.reference_images],
        revision_notes=user_input.revision_notes,
        parent_id=generation_id,
    )
    return RedirectResponse(f"/history/{child_id}", status_code=status.HTTP_303_SEE_OTHER)


async def _get_or_create_chat_session(chat_store: ChatStore, session_id: str | None) -> object:
    if session_id:
        session = await chat_store.get_session(session_id)
        if session:
            return session
    sessions = await chat_store.list_sessions(limit=20)
    if sessions:
        return sessions[0]
    return await chat_store.create_session(DEFAULT_CHAT_TITLE, CHAT_TEXT_MODELS[0]["id"])


async def _build_chat_context(
    request: Request,
    chat_store: ChatStore,
    session,
    error_message: str | None = None,
) -> dict:
    sessions = await chat_store.list_sessions(limit=50)
    session_cards: list[dict] = []
    for record in sessions:
        preview = await chat_store.first_user_message(record.id)
        label = record.title
        if (not label or label == DEFAULT_CHAT_TITLE) and preview:
            label = preview.content.strip()
        label = (label or "Untitled").strip()
        if len(label) > 60:
            label = f"{label[:57]}..."
        session_cards.append(
            {
                "id": record.id,
                "label": label,
                "created_at": record.created_at.strftime("%b %d"),
                "created_dt": record.created_at,
                "active": session and record.id == session.id,
            }
        )
    session_cards.sort(key=lambda item: item["created_dt"], reverse=True)
    messages = await chat_store.list_messages(session.id, limit=100)
    formatted_messages = []
    for msg in messages:
        attachments = summarize_attachments((msg.extra or {}).get("attachments") or [])
        formatted_messages.append(
            {
                "id": msg.id,
                "role": msg.role,
                "message_type": msg.message_type,
                "content": msg.content,
                "model": msg.model,
                "prompt": msg.prompt,
                "image_url": _public_path(msg.image_path),
                "parent_message_id": msg.parent_message_id,
                "created_at": msg.created_at.strftime("%b %d, %H:%M"),
                "attachments": _enrich_attachments(attachments),
            }
        )
    return {
        "request": request,
        "session_cards": session_cards,
        "active_session": session,
        "messages": formatted_messages,
        "text_models": CHAT_TEXT_MODELS,
        "image_models": CHAT_IMAGE_MODELS,
        "error_message": error_message,
        "prompt_suggestions": CHAT_SUGGESTIONS,
    }


def _build_chat_image_prompt(user_text: str, parent_message) -> str:
    base = ""
    if parent_message:
        base = parent_message.prompt or parent_message.content or ""
    if base:
        return f"Base visual description:\n{base}\n\nRefinement request:\n{user_text}"
    return user_text


def _enrich_attachments(items: list[dict]) -> list[dict]:
    for item in items:
        size_label = _format_size(item.get("size") or 0)
        mime = item.get("content_type") or ""
        item["meta"] = f"{size_label} · {mime}" if mime else size_label
    return items


def _build_model_payload(messages: list) -> list[dict]:
    payload: list[dict] = []
    for msg in messages:
        parts = [{"text": msg.content}]
        attachments_meta = (msg.extra or {}).get("attachments") if msg.extra else None
        for meta in attachments_meta or []:
            part = attachment_to_part(meta)
            if part:
                parts.append(part)
        payload.append(
            {
                "role": msg.role,
                "parts": parts,
            }
        )
    return payload


def _format_size(num: int) -> str:
    size = float(max(num, 0))
    units = ["B", "KB", "MB", "GB"]
    for index, unit in enumerate(units):
        if size < 1024 or index == len(units) - 1:
            if unit == "B":
                return f"{size:.0f}{unit}"
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"


async def _build_history_detail_context(request: Request, history: HistoryStore, record, error_message: str | None) -> dict:
    spec = InfographicSpec(**record.spec)
    children_records = await history.list_revision_chain(record.id)
    children = [
        {
            "id": child.id,
            "created_at": child.created_at.strftime("%b %d, %H:%M"),
            "revision_notes": child.revision_notes,
            "image_url": _public_path(child.image_path),
        }
        for child in children_records
    ]
    return {
        "request": request,
        "spec": spec,
        "prompt": record.prompt,
        "image_path": _public_path(record.image_path),
        "warnings": record.warnings,
        "generation_id": record.id,
        "permalink": f"/history/{record.id}",
        "children": children,
        "error_message": error_message,
    }

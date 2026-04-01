from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models.presets import PresetRepository
from app.models.specs import (
    InfographicSpec,
    ModelDescriptor,
    RenderResponse,
    SpecPreviewResponse,
    UserInput,
)
from app.services.gemini_client import GeminiImageClient
from app.services.history_store import HistoryStore
from app.services.model_capabilities import list_capabilities
from app.services.planner import InfographicPlanner
from app.services.prompt_composer import PromptComposer
from app.services.revision import RevisionService
from app.services.text_overlay import apply_overlay

router = APIRouter(prefix="/api", tags=["api"])
settings = get_settings()


def get_planner(request: Request) -> InfographicPlanner:
    return request.app.state.planner


def get_preset_repo(request: Request) -> PresetRepository:
    return request.app.state.preset_repo


def get_prompt_composer(request: Request) -> PromptComposer:
    return request.app.state.prompt_composer


def get_gemini_client(request: Request) -> GeminiImageClient:
    return request.app.state.gemini_client


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


@router.get("/models", response_model=List[ModelDescriptor])
async def list_models() -> List[ModelDescriptor]:
    return [
        ModelDescriptor(
            id=cap.id,
            display_name=cap.display_name,
            tier=cap.tier,
            strengths=cap.strengths,
            recommended_aspect_ratios=cap.recommended_aspect_ratios,
            max_size=cap.max_size,
            supports_overlay=cap.supports_overlay,
        )
        for cap in list_capabilities()
    ]


@router.get("/styles")
async def list_styles(presets: PresetRepository = Depends(get_preset_repo)) -> Any:
    return {"styles": [preset.model_dump() for preset in presets.list_styles()]}


@router.get("/infographics")
async def list_infographics(presets: PresetRepository = Depends(get_preset_repo)) -> Any:
    return {"infographics": [preset.model_dump() for preset in presets.list_infographics()]}


@router.get("/section-templates")
async def list_section_templates(presets: PresetRepository = Depends(get_preset_repo)) -> Any:
    return {"section_templates": [preset.model_dump() for preset in presets.list_section_templates()]}


@router.post("/spec/preview", response_model=SpecPreviewResponse)
async def create_spec_preview(
    payload: UserInput,
    planner: InfographicPlanner = Depends(get_planner),
) -> SpecPreviewResponse:
    spec = planner.plan(payload)
    return SpecPreviewResponse(spec=spec)


@router.post("/render", response_model=RenderResponse)
async def render_infographic(
    payload: UserInput,
    planner: InfographicPlanner = Depends(get_planner),
    composer: PromptComposer = Depends(get_prompt_composer),
    gemini: GeminiImageClient = Depends(get_gemini_client),
    history: HistoryStore = Depends(get_history_store),
) -> RenderResponse:
    spec = planner.plan(payload)
    prompt = composer.compose(spec)
    try:
        render_result = await gemini.generate_image(
            prompt=prompt,
            model=spec.selected_model,
            size=spec.image_size,
            aspect_ratio=spec.aspect_ratio,
            reference_images=spec.reference_images,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    image_path = render_result.image_path
    if spec.rendering_mode.value == "hybrid_overlay":
        image_path = apply_overlay(image_path, spec)

    generation_id = await history.save_generation(
        spec=spec,
        prompt=prompt,
        selected_model=spec.selected_model,
        rendering_mode=spec.rendering_mode.value,
        user_input=payload.model_dump(mode="json"),
        warnings=spec.warnings,
        image_path=image_path,
        reference_images=[ri.model_dump() for ri in spec.reference_images],
        revision_notes=payload.revision_notes,
        parent_id=payload.revision_of,
    )

    return RenderResponse(
        generation_id=generation_id,
        image_path=_public_path(image_path),
        spec=spec,
        warnings=spec.warnings,
    )


class RevisionPayload(UserInput):
    revision_notes: Optional[str] = None


@router.post("/revise/{generation_id}", response_model=RenderResponse)
async def revise_infographic(
    generation_id: str,
    payload: RevisionPayload,
    history: HistoryStore = Depends(get_history_store),
    planner: InfographicPlanner = Depends(get_planner),
    composer: PromptComposer = Depends(get_prompt_composer),
    gemini: GeminiImageClient = Depends(get_gemini_client),
) -> RenderResponse:
    record = await history.get_generation(generation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Generation not found")

    base_spec = InfographicSpec(**record.spec)
    revision_service = RevisionService()
    revised_input = revision_service.build_revision_input(base_spec, payload.model_dump(exclude_none=True))
    revised_input.revision_of = generation_id

    spec = planner.plan(revised_input)
    prompt = composer.compose(spec)
    try:
        render_result = await gemini.generate_image(
            prompt=prompt,
            model=spec.selected_model,
            size=spec.image_size,
            aspect_ratio=spec.aspect_ratio,
            reference_images=spec.reference_images,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    image_path = render_result.image_path
    if spec.rendering_mode.value == "hybrid_overlay":
        image_path = apply_overlay(image_path, spec)

    new_id = await history.save_generation(
        spec=spec,
        prompt=prompt,
        selected_model=spec.selected_model,
        rendering_mode=spec.rendering_mode.value,
        user_input=revised_input.model_dump(mode="json"),
        warnings=spec.warnings,
        image_path=image_path,
        reference_images=[ri.model_dump() for ri in spec.reference_images],
        revision_notes=payload.revision_notes,
        parent_id=generation_id,
    )

    return RenderResponse(
        generation_id=new_id,
        image_path=_public_path(image_path),
        spec=spec,
        warnings=spec.warnings,
    )


@router.get("/history")
async def list_history(history: HistoryStore = Depends(get_history_store)) -> Any:
    records = await history.list_generations()
    return {
        "items": [
            {
                "id": record.id,
                "request_id": record.request_id,
                "model": record.selected_model,
                "rendering_mode": record.rendering_mode,
                "warnings": record.warnings,
                "created_at": record.created_at,
                "image_path": _public_path(record.image_path),
            }
            for record in records
        ]
    }


@router.get("/history/{generation_id}")
async def get_history_item(generation_id: str, history: HistoryStore = Depends(get_history_store)) -> Any:
    record = await history.get_generation(generation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Generation not found")
    return {
        "id": record.id,
        "request_id": record.request_id,
        "spec": record.spec,
        "prompt": record.prompt,
        "model": record.selected_model,
        "rendering_mode": record.rendering_mode,
        "warnings": record.warnings,
        "image_path": _public_path(record.image_path),
        "reference_images": record.reference_images,
        "revision_notes": record.revision_notes,
        "parent_id": record.parent_id,
        "created_at": record.created_at,
    }

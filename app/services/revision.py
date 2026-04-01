from __future__ import annotations

import uuid
from typing import Any, Dict

from app.models.specs import InfographicSpec, UserInput


class RevisionService:
    def build_revision_input(self, base_spec: InfographicSpec, overrides: Dict[str, Any]) -> UserInput:
        data = {
            "request_id": overrides.get("request_id", str(uuid.uuid4())),
            "topic": overrides.get("topic", base_spec.topic),
            "audience": overrides.get("audience", base_spec.audience),
            "desired_model": overrides.get("desired_model", base_spec.selected_model),
            "infographic_type": overrides.get("infographic_type", base_spec.infographic_type),
            "visual_style": overrides.get("visual_style", base_spec.visual_style),
            "title": overrides.get("title", base_spec.title),
            "subtitle": overrides.get("subtitle", base_spec.subtitle),
            "sections": overrides.get("sections", base_spec.sections),
            "footer_text": overrides.get("footer_text", base_spec.footer_text),
            "aspect_ratio": overrides.get("aspect_ratio", base_spec.aspect_ratio),
            "image_size": overrides.get("image_size", base_spec.image_size),
            "exact_text_required": overrides.get("exact_text_required", base_spec.exact_text_required),
            "text_preference": overrides.get(
                "text_preference", "exact" if not base_spec.text_can_be_summarized else "summarize"
            ),
            "palette": overrides.get("palette", base_spec.palette),
            "reference_images": overrides.get("reference_images", base_spec.reference_images),
            "render_mode": overrides.get("render_mode", base_spec.rendering_mode),
            "revision_of": base_spec.request_id,
            "revision_notes": overrides.get("revision_notes"),
        }
        return UserInput(**data)

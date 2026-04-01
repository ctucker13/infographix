from __future__ import annotations

from slugify import slugify

from app.models.presets import PresetRepository
from app.models.specs import InfographicSpec, RenderingMode, UserInput
from app.services.model_capabilities import get_capability
from app.services.text_budget import evaluate_text_budget


class InfographicPlanner:
    def __init__(self, presets: PresetRepository):
        self.presets = presets

    def plan(self, user_input: UserInput) -> InfographicSpec:
        style = self.presets.get_style(user_input.visual_style)
        infographic = self.presets.get_infographic(user_input.infographic_type)
        desired_model = user_input.desired_model or "models/gemini-2.5-flash-image"
        capability = get_capability(desired_model)
        recommended_model = self._recommend_model(user_input)

        aspect_ratio = user_input.aspect_ratio or infographic.recommended_aspect_ratios[0]
        image_size = user_input.image_size or ("1024x1024" if capability.id.endswith("2.5-flash-image") else "2048x2048")

        spec = InfographicSpec(
            request_id=user_input.request_id,
            topic=user_input.topic,
            audience=user_input.audience,
            selected_model=desired_model,
            recommended_model=recommended_model,
            infographic_type=user_input.infographic_type,
            visual_style=user_input.visual_style,
            title=user_input.title or slugify(user_input.topic, separator=" ").title(),
            subtitle=user_input.subtitle,
            sections=user_input.sections,
            footer_text=user_input.footer_text,
            palette=user_input.palette,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            use_reference_images=bool(user_input.reference_images),
            reference_images=user_input.reference_images,
            exact_text_required=user_input.exact_text_required,
            text_can_be_summarized=user_input.text_preference != "exact",
            rendering_mode=self._pick_rendering_mode(user_input),
            revision_notes=user_input.revision_notes,
            metadata={
                "style_summary": style.summary,
                "infographic_summary": infographic.summary,
            },
        )

        status, warnings, density = evaluate_text_budget(spec)
        spec.text_budget_status = status
        spec.warnings = warnings
        spec.composition_density = density

        if spec.rendering_mode == RenderingMode.HYBRID_OVERLAY:
            spec.warnings.append("Hybrid overlay recommended for text-heavy content.")

        return spec

    def _recommend_model(self, user_input: UserInput) -> str:
        if user_input.exact_text_required or any(
            len(block.body) > 60 for section in user_input.sections for block in section.text_blocks
        ):
            return "models/gemini-3.1-flash-image-preview"
        return user_input.desired_model or "models/gemini-2.5-flash-image"

    def _pick_rendering_mode(self, user_input: UserInput) -> RenderingMode:
        if user_input.render_mode:
            return user_input.render_mode
        if user_input.exact_text_required:
            return RenderingMode.HYBRID_OVERLAY
        heavy_sections = sum(len(block.body) for s in user_input.sections for block in s.text_blocks) > 800
        return RenderingMode.HYBRID_OVERLAY if heavy_sections else RenderingMode.PURE_IMAGE

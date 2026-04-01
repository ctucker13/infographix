from __future__ import annotations

import json

from app.models.presets import PresetRepository
from app.models.specs import InfographicSpec
from app.services import prompt_fragments


class PromptComposer:
    def __init__(self, presets: PresetRepository):
        self.presets = presets

    def compose(self, spec: InfographicSpec) -> str:
        style = self.presets.get_style(spec.visual_style)
        infographic = self.presets.get_infographic(spec.infographic_type)

        fragments: list[str] = []
        fragments += prompt_fragments.build_global_fragments(spec)
        fragments += prompt_fragments.build_style_fragments(style)
        if spec.custom_visual_style:
            fragments.append(f"Visual style guidance: {spec.custom_visual_style}")
        fragments += prompt_fragments.build_infographic_fragments(infographic)
        fragments += prompt_fragments.build_section_fragments(spec.sections)
        fragments += prompt_fragments.build_text_handling_fragments(spec)

        fragments += style.prompt_fragments.get("global", [])
        fragments += infographic.prompt_fragments.get("global", [])
        fragments += style.prompt_fragments.get("negative", [])
        fragments += infographic.prompt_fragments.get("negative", [])

        if spec.palette:
            fragments.append(
                f"Palette: primary {spec.palette.primary}, secondary {spec.palette.secondary}, accent {spec.palette.accent}, background {spec.palette.background}, text {spec.palette.text}."
            )
        if spec.background_style:
            fragments.append(f"Background treatment: {spec.background_style}.")

        prompt_body = "\n".join(f"- {fragment}" for fragment in fragments if fragment.strip())

        copy_lines: list[str] = [
            "Design a production-ready infographic. Use the copy specified below and do not reproduce meta labels such as 'Title', 'Subtitle', or 'Section' within the artwork.",
        ]
        if spec.title:
            copy_lines.append(f"Render the primary headline exactly as {json.dumps(spec.title)}.")
        if spec.subtitle:
            copy_lines.append(f"Use the subtitle {json.dumps(spec.subtitle)} beneath the title.")
        if spec.footer_text:
            copy_lines.append(f"Place footer or source text reading {json.dumps(spec.footer_text)}.")
        if spec.revision_notes:
            copy_lines.append(f"Revision instructions: {json.dumps(spec.revision_notes)}.")

        header = "\n".join(copy_lines).strip()
        if prompt_body:
            return f"{header}\n{prompt_body}"
        return header

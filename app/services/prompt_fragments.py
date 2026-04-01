from __future__ import annotations

from typing import List

from app.models.presets import InfographicPreset, StylePreset
from app.models.specs import InfographicSection, InfographicSpec


def _quote(text: str) -> str:
    return text.replace('"', '\\"')


def build_global_fragments(spec: InfographicSpec) -> List[str]:
    fragments = [
        f"Create a data-rich infographic about '{spec.topic}'.",
        f"Infographic type: {spec.infographic_type} with aspect ratio {spec.aspect_ratio} and image size {spec.image_size}.",
        f"Audience: {spec.audience or 'general'}. Maintain clear hierarchy and readable typography.",
        f"Rendering mode: {spec.rendering_mode.value}. Prioritize balanced composition with {spec.composition_density.value} density.",
        "Render only the actual copy provided. Never display placeholder labels such as 'Title', 'Subtitle', 'Section', or 'Label' on the artwork.",
    ]
    if spec.exact_text_required:
        fragments.append("Exact text for key labels must match the provided strings.")
    return fragments


def build_style_fragments(style: StylePreset) -> List[str]:
    fragments = [f"Apply {style.display_name} style: {style.summary}."]
    fragments.extend(style.rendering_rules)
    fragments.extend(style.color_behavior)
    fragments.extend(style.text_rules)
    return fragments


def build_infographic_fragments(preset: InfographicPreset) -> List[str]:
    fragments = [f"Follow layout guidance: {'; '.join(preset.layout_rules)}"]
    fragments.append(f"Section structure focus: {'; '.join(preset.section_structure)}")
    fragments.extend(preset.prompt_fragments.get("composition", []))
    return fragments


def build_section_fragments(sections: List[InfographicSection]) -> List[str]:
    fragments: List[str] = []
    for section in sections:
        descriptor = section.title or section.id
        section_lines: List[str] = [
            f"Section '{descriptor}' (id {section.id}) must read naturally and integrate with the chosen layout."
        ]
        if section.emphasis:
            section_lines.append(f"Emphasize {section.emphasis}.")
        if section.icon_hint:
            section_lines.append(f"Icon hint: {section.icon_hint}.")
        if section.chart_hint:
            section_lines.append(f"Chart/data hint: {section.chart_hint}.")

        for block in section.text_blocks:
            block_line = (
                f"Include a label reading \"{_quote(block.label)}\" paired with copy \"{_quote(block.body)}\"."
            )
            if block.exact_text:
                block_line += " Render this text exactly as written."
            elif not block.summarizable:
                block_line += " Keep the provided copy intact."
            else:
                block_line += " You may shorten slightly if space is tight."
            if block.decorative_only:
                block_line += " Treat as decorative lettering only."
            section_lines.append(block_line)

        fragments.append(" ".join(section_lines))
    return fragments


def build_text_handling_fragments(spec: InfographicSpec) -> List[str]:
    fragments = []
    if spec.text_can_be_summarized:
        fragments.append("Summarize long descriptive text into concise infographic labels.")
    else:
        fragments.append("All provided text must appear verbatim.")
    if spec.warnings:
        fragments.append("Warnings: mitigate clutter, obey text budget, prioritize legibility.")
    fragments.append("Avoid clutter, illegible typography, distorted text, low contrast, or repeated clip-art.")
    return fragments

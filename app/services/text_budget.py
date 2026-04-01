from __future__ import annotations

from typing import Tuple

from app.models.specs import InfographicSpec, TextBudgetStatus, TextDensity

TEXT_BUDGETS = {
    "vertical_timeline": {"max_sections": 6, "max_blocks": 4, "title_chars": 60, "label_chars": 45},
    "process_flow": {"max_sections": 5, "max_blocks": 5, "title_chars": 48, "label_chars": 40},
    "comparison_chart": {"max_sections": 4, "max_blocks": 6, "title_chars": 48, "label_chars": 38},
    "educational_diagram": {"max_sections": 5, "max_blocks": 5, "title_chars": 70, "label_chars": 50},
    "statistical_infographic": {"max_sections": 6, "max_blocks": 6, "title_chars": 65, "label_chars": 42},
    "mind_map": {"max_sections": 8, "max_blocks": 3, "title_chars": 32, "label_chars": 28},
    "whiteboard_explainer": {"max_sections": 5, "max_blocks": 6, "title_chars": 58, "label_chars": 44},
    "line_art_infographic": {"max_sections": 4, "max_blocks": 4, "title_chars": 40, "label_chars": 36},
    "concept_diagram": {"max_sections": 5, "max_blocks": 4, "title_chars": 54, "label_chars": 38},
    "roadmap": {"max_sections": 6, "max_blocks": 3, "title_chars": 62, "label_chars": 36},
    "scientific_illustration": {"max_sections": 5, "max_blocks": 5, "title_chars": 68, "label_chars": 48},
    "explainer_graphic": {"max_sections": 5, "max_blocks": 5, "title_chars": 60, "label_chars": 40},
}


def evaluate_text_budget(spec: InfographicSpec) -> Tuple[TextBudgetStatus, list[str], TextDensity]:
    rules = TEXT_BUDGETS.get(spec.infographic_type, TEXT_BUDGETS["explainer_graphic"])
    warnings: list[str] = []

    if spec.title and len(spec.title) > rules["title_chars"]:
        warnings.append(
            f"Title length {len(spec.title)} exceeds recommended {rules['title_chars']} characters."
        )

    if len(spec.sections) > rules["max_sections"]:
        warnings.append(
            f"Section count {len(spec.sections)} exceeds recommended {rules['max_sections']}."
        )

    for section in spec.sections:
        if len(section.text_blocks) > rules["max_blocks"]:
            warnings.append(
                f"Section {section.id} has {len(section.text_blocks)} text blocks; recommend {rules['max_blocks']} or fewer."
            )
        for block in section.text_blocks:
            if len(block.body) > rules["label_chars"]:
                warnings.append(
                    f"Text block '{block.label}' may be too long ({len(block.body)} chars)."
                )

    if warnings:
        status = TextBudgetStatus.AT_RISK if len(warnings) <= 2 else TextBudgetStatus.OVER_LIMIT
    else:
        status = TextBudgetStatus.WITHIN_LIMITS

    density = TextDensity.BALANCED
    if status == TextBudgetStatus.OVER_LIMIT:
        density = TextDensity.HEAVY
    elif status == TextBudgetStatus.WITHIN_LIMITS and len(spec.sections) <= (rules["max_sections"] // 2):
        density = TextDensity.LIGHT

    return status, warnings, density

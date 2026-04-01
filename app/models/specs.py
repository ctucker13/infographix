from __future__ import annotations

from enum import Enum
from typing import Any, List

from pydantic import BaseModel, Field


class ReferenceImageRole(str, Enum):
    STYLE = "style_reference"
    CHARACTER = "character_reference"
    OBJECT = "object_reference"
    BRANDING = "branding_reference"
    LAYOUT = "layout_inspiration"


class ReferenceImageSpec(BaseModel):
    id: str
    filename: str
    content_type: str
    role: ReferenceImageRole
    path: str


class TextDensity(str, Enum):
    LIGHT = "light"
    BALANCED = "balanced"
    HEAVY = "heavy"


class TextBudgetStatus(str, Enum):
    WITHIN_LIMITS = "within_limits"
    AT_RISK = "at_risk"
    OVER_LIMIT = "over_limit"


class RenderingMode(str, Enum):
    PURE_IMAGE = "pure_image"
    HYBRID_OVERLAY = "hybrid_overlay"


class TextBlock(BaseModel):
    label: str
    body: str
    exact_text: bool = False
    summarizable: bool = True
    decorative_only: bool = False


class InfographicSection(BaseModel):
    id: str
    title: str | None = None
    emphasis: str | None = None
    text_blocks: List[TextBlock] = Field(default_factory=list)
    notes: str | None = None
    icon_hint: str | None = None
    chart_hint: str | None = None


class PaletteSpec(BaseModel):
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    contrast_notes: str | None = None


class LayoutSpec(BaseModel):
    aspect_ratio: str = "1:1"
    recommended_grid: str | None = None
    spacing_notes: str | None = None
    visual_density: str | None = None


class InfographicSpec(BaseModel):
    request_id: str
    topic: str
    audience: str | None
    selected_model: str
    recommended_model: str
    infographic_type: str
    visual_style: str
    title: str | None = None
    subtitle: str | None = None
    sections: List[InfographicSection] = Field(default_factory=list)
    footer_text: str | None = None
    icon_hints: List[str] = Field(default_factory=list)
    chart_hints: List[str] = Field(default_factory=list)
    palette: PaletteSpec | None = None
    background_style: str | None = None
    composition_density: TextDensity = TextDensity.BALANCED
    aspect_ratio: str = "1:1"
    image_size: str = "1024x1024"
    use_reference_images: bool = False
    reference_images: List[ReferenceImageSpec] = Field(default_factory=list)
    exact_text_required: bool = False
    text_can_be_summarized: bool = True
    text_budget_status: TextBudgetStatus = TextBudgetStatus.WITHIN_LIMITS
    rendering_mode: RenderingMode = RenderingMode.PURE_IMAGE
    revision_notes: str | None = None
    warnings: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserInput(BaseModel):
    request_id: str
    topic: str
    audience: str | None = None
    desired_model: str | None = None
    infographic_type: str
    visual_style: str
    title: str | None = None
    subtitle: str | None = None
    sections: List[InfographicSection] = Field(default_factory=list)
    footer_text: str | None = None
    aspect_ratio: str | None = None
    image_size: str | None = None
    exact_text_required: bool = False
    text_preference: str | None = None
    palette: PaletteSpec | None = None
    reference_images: List[ReferenceImageSpec] = Field(default_factory=list)
    render_mode: RenderingMode | None = None
    revision_of: str | None = None
    revision_notes: str | None = None


class SpecPreviewResponse(BaseModel):
    spec: InfographicSpec


class RenderResponse(BaseModel):
    generation_id: str
    image_path: str | None
    spec: InfographicSpec
    warnings: List[str]


class ModelDescriptor(BaseModel):
    id: str
    display_name: str
    tier: str
    strengths: List[str]
    recommended_aspect_ratios: List[str]
    max_size: str
    supports_overlay: bool


class PresetListResponse(BaseModel):
    styles: List[dict[str, Any]]
    infographic_types: List[dict[str, Any]]

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import yaml
from pydantic import BaseModel, Field


class PresetFragment(BaseModel):
    summary: str
    instructions: List[str] = Field(default_factory=list)


class StylePreset(BaseModel):
    id: str
    display_name: str
    summary: str
    rendering_rules: List[str]
    text_rules: List[str]
    color_behavior: List[str]
    recommended_use_cases: List[str]
    negative_rules: List[str]
    prompt_fragments: Dict[str, List[str]]


class InfographicPreset(BaseModel):
    id: str
    display_name: str
    summary: str
    recommended_aspect_ratios: List[str]
    layout_rules: List[str]
    section_structure: List[str]
    text_budget_guidance: List[str]
    recommended_icon_density: str
    recommended_chart_density: str
    prompt_fragments: Dict[str, List[str]]


class SectionTemplateBlock(BaseModel):
    label: str
    body: str
    exact_text: bool = False
    summarizable: bool = True
    decorative_only: bool = False


class SectionTemplateSection(BaseModel):
    id: str
    title: str
    icon_hint: str | None = None
    chart_hint: str | None = None
    text_blocks: List[SectionTemplateBlock] = Field(default_factory=list)


class SectionTemplate(BaseModel):
    id: str
    display_name: str
    summary: str
    recommended_for: List[str] = Field(default_factory=list)
    guidance: List[str] = Field(default_factory=list)
    default_aspect_ratio: str | None = None
    default_image_size: str | None = None
    sections: List[SectionTemplateSection] = Field(default_factory=list)


class PresetRepository:
    def __init__(self, style_dir: Path, infographic_dir: Path, section_template_dir: Path | None = None):
        self.style_dir = style_dir
        self.infographic_dir = infographic_dir
        self.section_template_dir = section_template_dir
        self.styles: Dict[str, StylePreset] = {}
        self.infographics: Dict[str, InfographicPreset] = {}
        self.section_templates: Dict[str, SectionTemplate] = {}

    def load(self) -> None:
        self.styles = {preset.id: preset for preset in self._read_presets(self.style_dir, StylePreset)}
        self.infographics = {
            preset.id: preset for preset in self._read_presets(self.infographic_dir, InfographicPreset)
        }
        if self.section_template_dir:
            self.section_templates = {
                preset.id: preset
                for preset in self._read_presets(self.section_template_dir, SectionTemplate)
            }
        else:
            self.section_templates = {}

    def _read_presets(self, directory: Path, model: type[BaseModel]) -> Iterable[BaseModel]:
        presets: list[BaseModel] = []
        if not directory.exists():
            return presets
        for file in sorted(directory.glob("*.yaml")):
            with file.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
            presets.append(model(**data))
        return presets

    def get_style(self, preset_id: str) -> StylePreset:
        return self.styles[preset_id]

    def get_infographic(self, preset_id: str) -> InfographicPreset:
        return self.infographics[preset_id]

    def list_styles(self) -> List[StylePreset]:
        return list(self.styles.values())

    def list_infographics(self) -> List[InfographicPreset]:
        return list(self.infographics.values())

    def get_section_template(self, template_id: str) -> SectionTemplate:
        return self.section_templates[template_id]

    def list_section_templates(self) -> List[SectionTemplate]:
        return list(self.section_templates.values())

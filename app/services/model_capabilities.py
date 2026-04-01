from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(slots=True)
class ModelCapability:
    id: str
    display_name: str
    tier: str
    strengths: List[str]
    recommended_aspect_ratios: List[str]
    max_size: str
    supported_sizes: List[str]
    supports_overlay: bool
    max_reference_images: int
    text_strength: str
    recommended_use: str


MODEL_CAPABILITIES: Dict[str, ModelCapability] = {
    "models/gemini-2.5-flash-image": ModelCapability(
        id="models/gemini-2.5-flash-image",
        display_name="Gemini 2.5 Flash Image",
        tier="low-latency",
        strengths=["fast", "budget-friendly", "simple layouts"],
        recommended_aspect_ratios=["1:1", "3:2", "4:3", "16:9"],
        max_size="2K",
        supported_sizes=["1K", "2K"],
        supports_overlay=True,
        max_reference_images=4,
        text_strength="medium",
        recommended_use="high-volume marketing, quick drafts",
    ),
    "models/gemini-3.1-flash-image-preview": ModelCapability(
        id="models/gemini-3.1-flash-image-preview",
        display_name="Gemini 3.1 Flash Image Preview",
        tier="premium",
        strengths=[
            "advanced aspect ratios",
            "higher resolution",
            "stronger typography",
        ],
        recommended_aspect_ratios=["1:1", "2:3", "3:2", "9:16", "16:9"],
        max_size="4K",
        supported_sizes=["1K", "2K", "4K"],
        supports_overlay=True,
        max_reference_images=14,
        text_strength="high",
        recommended_use="text-heavy infographics, hero assets",
    ),
}


def list_capabilities() -> List[ModelCapability]:
    return list(MODEL_CAPABILITIES.values())


def get_capability(model_id: str) -> ModelCapability:
    return MODEL_CAPABILITIES[model_id]

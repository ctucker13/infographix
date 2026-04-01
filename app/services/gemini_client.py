from __future__ import annotations

import uuid
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import List

import anyio

from app.config import get_settings
from app.models.specs import ReferenceImageSpec

try:  # pragma: no cover - import guard
    from google import genai
    from google.genai import types as genai_types
except Exception:  # pragma: no cover
    genai = None
    genai_types = None

ALLOWED_ASPECT_RATIOS = {
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "9:16",
    "16:9",
    "21:9",
}


@dataclass(slots=True)
class ImageRenderResult:
    image_path: str
    model: str
    prompt: str


class GeminiImageClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = None
        if self.settings.google_api_key and genai:
            self.client = genai.Client(api_key=self.settings.google_api_key)

    async def generate_image(
        self,
        prompt: str,
        model: str,
        size: str,
        aspect_ratio: str,
        reference_images: List[ReferenceImageSpec] | None = None,
    ) -> ImageRenderResult:
        if not self.client or not genai_types:
            raise RuntimeError(
                "Gemini client is not configured. Set a valid GOOGLE_API_KEY to enable rendering."
            )

        target = self.settings.storage_path / "outputs" / f"{uuid.uuid4()}.png"
        config = genai_types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=genai_types.ImageConfig(
                aspect_ratio=aspect_ratio if aspect_ratio in ALLOWED_ASPECT_RATIOS else None,
                image_size=_normalize_image_size(size),
            ),
        )
        try:
            response = await anyio.to_thread.run_sync(
                lambda: self.client.models.generate_content(
                    model=model,
                    contents=[{"parts": [{"text": prompt}]}],
                    config=config,
                )
            )
        except Exception as exc:  # pragma: no cover - SDK/runtime issues
            raise RuntimeError(f"Gemini image generation failed: {exc}") from exc

        raw = _extract_first_image_bytes(response)
        if not raw:
            raise RuntimeError("Gemini response did not include binary image data.")

        with target.open("wb") as handle:
            handle.write(raw)

        return ImageRenderResult(image_path=str(target), model=model, prompt=prompt)


def _normalize_image_size(image_size: str | None) -> str:
    if not image_size:
        return "1K"
    try:
        width = int(image_size.lower().split("x")[0])
    except (ValueError, AttributeError):
        return "1K"
    if width >= 3000:
        return "4K"
    if width >= 1800:
        return "2K"
    return "1K"


def _extract_first_image_bytes(response: object) -> bytes | None:
    candidates = _get_attr_or_key(response, "candidates") or []
    for candidate in candidates:
        content = _get_attr_or_key(candidate, "content")
        if not content:
            continue
        parts = _get_attr_or_key(content, "parts") or []
        for part in parts:
            inline = _get_attr_or_key(part, "inline_data")
            if inline and (_get_attr_or_key(inline, "mime_type") or "").startswith("image/"):
                data = _get_attr_or_key(inline, "data")
                if data:
                    return _coerce_to_bytes(data)

    # Fallback: search the entire response dict for inline_data entries
    dump = getattr(response, "model_dump", None)
    if callable(dump):
        stack = [dump()]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                inline = node.get("inline_data")
                if inline:
                    data = inline.get("data")
                    if data:
                        return _coerce_to_bytes(data)
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return None


def _get_attr_or_key(obj: object, key: str):
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key)
    return None


def _coerce_to_bytes(value: object) -> bytes | None:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        try:
            return base64.b64decode(value)
        except Exception:
            return value.encode("utf-8")
    return None

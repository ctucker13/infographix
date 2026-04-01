from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.models.specs import InfographicSpec


def apply_overlay(image_path: str, spec: InfographicSpec) -> str:
    """Draw deterministic text labels onto the generated image."""
    overlay_lines = _collect_overlay_lines(spec)
    if not overlay_lines:
        return image_path

    image = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    width, height = image.size

    padding_x = 40
    cursor_y = 40
    for label, text in overlay_lines:
        content = f"{label}: {text}" if label else text
        wrapped = _truncate(content, max_chars=85)
        draw.text((padding_x, cursor_y), wrapped, fill="white", font=font)
        cursor_y += 22
        if cursor_y > height - 40:
            break

    output_path = Path(image_path)
    image.save(output_path)
    return str(output_path)


def _collect_overlay_lines(spec: InfographicSpec) -> list[tuple[str | None, str]]:
    lines: list[tuple[str | None, str]] = []
    if spec.exact_text_required:
        if spec.title:
            lines.append((None, spec.title))
        if spec.subtitle:
            lines.append((None, spec.subtitle))
        if spec.footer_text:
            lines.append((None, spec.footer_text))
    for section in spec.sections:
        blocks = [block for block in section.text_blocks if block.exact_text]
        if not blocks:
            continue
        if section.title:
            lines.append((None, section.title))
        for block in blocks:
            lines.append((block.label, block.body))
    return lines


def _truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1] + "…"

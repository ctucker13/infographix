from __future__ import annotations

from textwrap import dedent
from typing import Sequence

import anyio

from app.config import get_settings
from app.models.chat import ChatResponseMode

try:  # pragma: no cover
    from google import genai
except Exception:  # pragma: no cover
    genai = None


class GeminiTextClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = None
        if self.settings.google_api_key and genai:
            self.client = genai.Client(api_key=self.settings.google_api_key)

    async def generate_reply(self, model: str, messages: Sequence[dict]) -> str:
        if not self.client:
            raise RuntimeError("Gemini text client is not configured. Set GOOGLE_API_KEY to enable chat.")

        contents = []
        for message in messages:
            role = message.get("role", "user")
            parts = message.get("parts")
            if not parts:
                parts = [{"text": message.get("content", "")}]
            contents.append({"role": role, "parts": parts})

        try:
            response = await anyio.to_thread.run_sync(
                lambda: self.client.models.generate_content(
                    model=model,
                    contents=contents,
                )
            )
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Gemini chat generation failed: {exc}") from exc

        return _extract_text(response) or ""

    async def generate_meta_prompt(self, model: str, messages: Sequence[dict]) -> str:
        if not self.client:
            raise RuntimeError(
                "Gemini text client is not configured. Set GOOGLE_API_KEY to enable meta-prompting."
            )

        guide = dedent(
            """
            You are Infographix Meta Prompt assistant. Your job is to gather enough structured context
            to populate Infographix's infographic request JSON. Follow these rules:
            1. If important fields are missing, ask targeted follow-up questions instead of guessing.
            2. Once you have enough detail, respond with:
               META PROMPT READY
               ```json
               { ...structured JSON... }
               ```
               followed by a short checklist of highlights.

            JSON schema (fill what you know, omit nulls):
            {
              "topic": "",
              "audience": "",
              "desired_model": "models/gemini-2.5-flash-image",
              "infographic_type": "",
              "visual_style": "",
              "title": "",
              "subtitle": "",
              "footer_text": "",
              "aspect_ratio": "16:9",
              "image_size": "1920x1080",
              "exact_text_required": false,
              "text_preference": "summarize",
              "render_mode": "pure_image",
              "sections": [
                {
                  "id": "slug-case",
                  "title": "",
                  "emphasis": "",
                  "icon_hint": "",
                  "chart_hint": "",
                  "text_blocks": [
                    {"label": "", "body": "", "exact_text": false}
                  ]
                }
              ],
              "reference_image_hints": [
                {"role": "style_reference", "notes": "what to borrow from the image"}
              ]
            }

            Section ids must be slug-like (letters, numbers, hyphen). Keep text blocks concise.
            """
        ).strip()

        contents = [
            {
                "role": "user",
                "parts": [{"text": guide}],
            }
        ]
        contents.extend(messages or [])

        try:
            response = await anyio.to_thread.run_sync(
                lambda: self.client.models.generate_content(
                    model=model,
                    contents=contents,
                )
            )
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Gemini meta prompt generation failed: {exc}") from exc

        return _extract_text(response) or ""

    async def detect_response_mode(
        self,
        prompt: str,
        attachments: list[dict] | None = None,
    ) -> ChatResponseMode:
        prompt = (prompt or "").strip()
        score = _estimate_visual_score(prompt, attachments or [])
        if score <= 0:
            return ChatResponseMode.TEXT
        if score >= 2:
            return ChatResponseMode.IMAGE
        if not self.client:
            return ChatResponseMode.TEXT
        classifier_prompt = (
            "Classify the user's intent as either TEXT or IMAGE. "
            "Respond with a single word: TEXT if the best response should be written language, "
            "or IMAGE if the user is asking for an illustration/visual render."
        )
        attachment_hint = ""
        if attachments:
            kinds = ", ".join(
                sorted({(meta.get("content_type") or "").split("/")[0] or "file" for meta in attachments})
            )
            attachment_hint = f"\nUser also attached: {kinds}."
        payload = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"{classifier_prompt}\n\nRequest:\n{prompt or '(empty)'}{attachment_hint}",
                    }
                ],
            }
        ]
        try:
            response = await anyio.to_thread.run_sync(
                lambda: self.client.models.generate_content(
                    model=self.settings.chat_router_model,
                    contents=payload,
                )
            )
        except Exception:
            return ChatResponseMode.TEXT
        verdict = (_extract_text(response) or "").strip().upper()
        return ChatResponseMode.IMAGE if verdict.startswith("IMAGE") else ChatResponseMode.TEXT


def _extract_text(response: object) -> str | None:
    text = []
    candidates = getattr(response, "candidates", []) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if parts:
            for part in parts:
                part_text = getattr(part, "text", None) or part.get("text") if isinstance(part, dict) else None
                if part_text:
                    text.append(part_text)
    if text:
        return "\n".join(text).strip()
    # fallback if response exposes model_dump
    dump = getattr(response, "model_dump", None)
    if callable(dump):
        data = dump()
        return _search_text(data)
    return None


def _search_text(node: object) -> str | None:
    if isinstance(node, dict):
        if "text" in node and isinstance(node["text"], str):
            return node["text"]
        for value in node.values():
            found = _search_text(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _search_text(value)
            if found:
                return found
    return None


def _estimate_visual_score(prompt: str, attachments: list[dict]) -> int:
    text = prompt.lower()
    hits = 0
    visual_keywords = [
        "draw",
        "illustrat",
        "infographic",
        "diagram",
        "render",
        "visualize",
        "poster",
        "logo",
        "cover art",
        "storyboard",
        "sketch",
        "moodboard",
    ]
    for keyword in visual_keywords:
        if keyword in text:
            hits += 1
    textual_keywords = ["explain", "summarize", "write", "document", "notes"]
    for keyword in textual_keywords:
        if keyword in text:
            hits -= 1
    for meta in attachments:
        mime = meta.get("content_type") or ""
        if mime.startswith("image/"):
            hits += 1
    return hits

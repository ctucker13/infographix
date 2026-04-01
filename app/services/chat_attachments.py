from __future__ import annotations

import base64
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from fastapi import UploadFile

from app.config import get_settings

TEXT_LIKE_MIME = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
    "application/xml",
}


@dataclass(slots=True)
class ChatAttachment:
    path: str
    original_name: str
    content_type: str
    size: int


def _sanitize_name(name: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip())
    return clean[:80] or "upload"


async def save_chat_attachment(upload: UploadFile) -> ChatAttachment | None:
    settings = get_settings()
    payload = await upload.read()
    if not payload:
        return None
    if len(payload) > settings.max_upload_bytes:
        raise ValueError(
            f"Attachment '{upload.filename}' exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB limit."
        )
    filename = f"{uuid.uuid4()}_{_sanitize_name(upload.filename or 'upload')}"
    target = settings.storage_path / "chat_uploads" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return ChatAttachment(
        path=str(target),
        original_name=upload.filename or "upload",
        content_type=upload.content_type or "application/octet-stream",
        size=len(payload),
    )


def attachment_to_part(meta: dict) -> dict | None:
    path = meta.get("path")
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        return None
    mime = meta.get("content_type") or "application/octet-stream"
    name = meta.get("original_name") or file_path.name
    data = file_path.read_bytes()
    if _is_textual(mime):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1", errors="ignore")
        snippet = text[:4000]
        if len(text) > 4000:
            snippet = f"{snippet}\n...[truncated attachment]..."
        return {
            "text": f"[Attachment: {name}]\n{snippet}",
        }
    encoded = base64.b64encode(data).decode("ascii")
    return {
        "inline_data": {
            "mime_type": mime,
            "data": encoded,
        }
    }


def _is_textual(mime: str) -> bool:
    if mime.startswith("text/"):
        return True
    return mime in TEXT_LIKE_MIME


def summarize_attachments(metas: Iterable[dict]) -> list[dict]:
    summary = []
    for meta in metas:
        path = meta.get("path")
        if not path:
            continue
        summary.append(
            {
                "name": meta.get("original_name") or Path(path).name,
                "url": _public_url(path),
                "size": meta.get("size") or 0,
                "content_type": meta.get("content_type") or "application/octet-stream",
            }
        )
    return summary


def _public_url(path: str) -> str | None:
    settings = get_settings()
    base = settings.storage_path.resolve()
    try:
        rel = Path(path).resolve().relative_to(base)
    except ValueError:
        return None
    return f"/storage/{rel.as_posix()}"

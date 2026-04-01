from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings
from app.models.specs import ReferenceImageRole, ReferenceImageSpec

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}


async def store_reference_image(upload: UploadFile, role: ReferenceImageRole) -> ReferenceImageSpec:
    settings = get_settings()
    if upload.content_type not in ALLOWED_TYPES:
        raise ValueError("Unsupported file type")

    raw = await upload.read()
    if len(raw) > settings.max_upload_bytes:
        raise ValueError("File too large")

    identifier = str(uuid.uuid4())
    extension = Path(upload.filename).suffix or ".png"
    target = settings.storage_path / "reference" / f"{identifier}{extension}"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as dest:
        dest.write(raw)

    return ReferenceImageSpec(
        id=identifier,
        filename=upload.filename,
        content_type=upload.content_type or "application/octet-stream",
        role=role,
        path=str(target),
    )

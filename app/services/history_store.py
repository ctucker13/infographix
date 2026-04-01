from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import GenerationRecord
from app.models.specs import InfographicSpec


class HistoryStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_generation(
        self,
        spec: InfographicSpec,
        prompt: str,
        selected_model: str,
        rendering_mode: str,
        user_input: dict,
        warnings: List[str],
        image_path: str | None,
        reference_images: list[dict] | None,
        revision_notes: str | None,
        parent_id: str | None,
    ) -> str:
        generation_id = str(uuid.uuid4())
        record = GenerationRecord(
            id=generation_id,
            request_id=spec.request_id,
            user_input=user_input,
            spec=spec.model_dump(mode="json"),
            prompt=prompt,
            selected_model=selected_model,
            rendering_mode=rendering_mode,
            warnings=warnings,
            image_path=image_path,
            reference_images=reference_images,
            revision_notes=revision_notes,
            parent_id=parent_id,
        )
        self.session.add(record)
        await self.session.commit()
        return generation_id

    async def list_generations(self, limit: int = 20) -> List[GenerationRecord]:
        stmt = select(GenerationRecord).order_by(GenerationRecord.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def get_generation(self, generation_id: str) -> GenerationRecord | None:
        stmt = select(GenerationRecord).where(GenerationRecord.id == generation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_revision_chain(self, generation_id: str) -> List[GenerationRecord]:
        stmt = (
            select(GenerationRecord)
            .where(GenerationRecord.parent_id == generation_id)
            .order_by(GenerationRecord.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import ChatMessage, ChatSession


class ChatStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, title: str, default_model: str) -> ChatSession:
        session_id = str(uuid.uuid4())
        record = ChatSession(
            id=session_id,
            title=title,
            default_model=default_model,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def list_sessions(self, limit: int = 20) -> List[ChatSession]:
        stmt = select(ChatSession).order_by(ChatSession.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def get_session(self, session_id: str) -> ChatSession | None:
        stmt = select(ChatSession).where(ChatSession.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_message(
        self,
        session_id: str,
        *,
        role: str,
        message_type: str,
        content: str,
        model: str,
        prompt: str | None = None,
        image_path: str | None = None,
        parent_message_id: str | None = None,
        extra: dict | None = None,
    ) -> ChatMessage:
        message_id = str(uuid.uuid4())
        record = ChatMessage(
            id=message_id,
            session_id=session_id,
            role=role,
            message_type=message_type,
            content=content,
            model=model,
            prompt=prompt,
            image_path=image_path,
            parent_message_id=parent_message_id,
            extra=extra or {},
        )
        self.session.add(record)
        await self.session.execute(
            ChatSession.__table__
            .update()
            .where(ChatSession.id == session_id)
            .values(updated_at=datetime.now(timezone.utc))
        )
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def list_messages(self, session_id: str, limit: int = 100) -> List[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def get_message(self, message_id: str) -> ChatMessage | None:
        stmt = select(ChatMessage).where(ChatMessage.id == message_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def first_user_message(self, session_id: str) -> ChatMessage | None:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id, ChatMessage.role == "user")
            .order_by(ChatMessage.created_at.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_session(self, session_id: str) -> bool:
        session = await self.get_session(session_id)
        if not session:
            return False
        await self.session.delete(session)
        await self.session.commit()
        return True

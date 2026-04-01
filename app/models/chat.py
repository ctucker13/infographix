from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ChatResponseMode(str, Enum):
    AUTO = "auto"
    TEXT = "text"
    IMAGE = "image"
    META_PROMPT = "meta_prompt"


class ChatMessageModel(BaseModel):
    id: str
    role: str
    message_type: ChatResponseMode
    content: str
    model: str
    prompt: Optional[str] = None
    image_path: Optional[str] = None
    parent_message_id: Optional[str] = None
    created_at: str
    attachments: Optional[list[dict]] = None


class ChatSessionModel(BaseModel):
    id: str
    title: str
    default_model: str


class ChatSendPayload(BaseModel):
    content: str
    response_mode: ChatResponseMode = ChatResponseMode.AUTO
    model_id: str
    parent_message_id: str | None = None

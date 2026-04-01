import pytest

from app.db import async_session, init_db
from app.services.chat_store import ChatStore


@pytest.mark.anyio
async def test_chat_store_creates_sessions_and_messages():
    await init_db()
    async with async_session() as session:
        store = ChatStore(session)
        chat_session = await store.create_session("Test chat", "models/gemini-2.5-pro")
        assert chat_session.title == "Test chat"

        user_msg = await store.add_message(
            chat_session.id,
            role="user",
            message_type="text",
            content="Hello world",
            model="models/gemini-2.5-pro",
        )
        assert user_msg.content == "Hello world"

        assistant_msg = await store.add_message(
            chat_session.id,
            role="assistant",
            message_type="text",
            content="Hi there",
            model="models/gemini-2.5-pro",
        )
        assert assistant_msg.role == "assistant"

        messages = await store.list_messages(chat_session.id)
        assert len(messages) == 2

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from models.chat import ChatMessage, ConversationMemory
from repositories.base import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage]):
    def __init__(self):
        super().__init__(ChatMessage)

    async def get_user_chat_history(
        self, db: AsyncSession, user_id: int, *, limit: int = 50
    ) -> List[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        res = await db.execute(stmt)
        # Reverse to get chronological order (oldest first, latest last)
        history = list(res.scalars().all())
        history.reverse()
        return history

    async def create_chat_message(
        self, db: AsyncSession, *, user_id: int, role: str, content: str
    ) -> ChatMessage:
        db_obj = ChatMessage(
            user_id=user_id,
            role=role,
            content=content
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class ConversationMemoryRepository(BaseRepository[ConversationMemory]):
    def __init__(self):
        super().__init__(ConversationMemory)

    async def get_user_memories(
        self, db: AsyncSession, user_id: int, *, limit: int = 50
    ) -> List[ConversationMemory]:
        stmt = (
            select(ConversationMemory)
            .where(ConversationMemory.user_id == user_id)
            .order_by(desc(ConversationMemory.importance_score), desc(ConversationMemory.created_at))
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def create_memory(
        self, db: AsyncSession, *, user_id: int, conversation: str, summary: str, importance_score: float
    ) -> ConversationMemory:
        db_obj = ConversationMemory(
            user_id=user_id,
            conversation=conversation,
            summary=summary,
            importance_score=importance_score
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


chat_message_repository = ChatMessageRepository()
conversation_memory_repository = ConversationMemoryRepository()

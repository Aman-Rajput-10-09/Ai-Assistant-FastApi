from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# --- Chat Message Schemas ---
class ChatMessageBase(BaseModel):
    role: str  # user, assistant, system
    content: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageRead(ChatMessageBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Conversation Memory Schemas ---
class ConversationMemoryBase(BaseModel):
    conversation: str
    summary: str
    importance_score: float = 1.0


class ConversationMemoryCreate(ConversationMemoryBase):
    pass


class ConversationMemoryRead(ConversationMemoryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

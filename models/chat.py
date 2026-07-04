from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from pgvector.sqlalchemy import Vector
from core.database import Base

if TYPE_CHECKING:
    from models.user import User


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(String(4000), nullable=False)
    
    # pgvector embedding for semantic search in history
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="chat_messages")


class ConversationMemory(Base):
    __tablename__ = "conversation_memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    conversation: Mapped[str] = mapped_column(String(4000), nullable=False) # original snippet or dialogue context
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)      # key facts/insights extracted
    importance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False) # 1.0 to 10.0 scale
    
    # pgvector embedding for semantic search
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memories")

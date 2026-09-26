from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
from pgvector.sqlalchemy import Vector
from core.database import Base

if TYPE_CHECKING:
    from models.user import User
    from models.category import Category
    from models.reminder import Reminder


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default="normal", nullable=False)  # low, normal, high
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, completed
    
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    
    # Interaction frequency tracking for Context Builder ranking
    interaction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # pgvector embedding column (768 dimensions for Gemini API embeddings)
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
    user: Mapped["User"] = relationship(back_populates="tasks")
    category: Mapped[Optional["Category"]] = relationship(back_populates="tasks")
    reminders: Mapped[List["Reminder"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    recurring_rules: Mapped[List["RecurringTask"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    attachments: Mapped[List["Attachment"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class RecurringTask(Base):
    __tablename__ = "recurring_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    
    recurrence_pattern: Mapped[str] = mapped_column(String(50), nullable=False)  # daily, weekly, monthly, yearly
    interval: Mapped[int] = mapped_column(Integer, default=1, nullable=False) # every N patterns (e.g. every 2 weeks)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 0-6 (Sunday-Saturday)
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 1-31

    # Relationships
    task: Mapped["Task"] = relationship(back_populates="recurring_rules")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    task: Mapped["Task"] = relationship(back_populates="attachments")

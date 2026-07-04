from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str
    color: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Reminder Schemas ---
class ReminderBase(BaseModel):
    title: str
    reminder_time: datetime
    method: str = "notification"


class ReminderCreate(ReminderBase):
    task_id: Optional[int] = None


class ReminderRead(ReminderBase):
    id: int
    user_id: int
    task_id: Optional[int] = None
    is_sent: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Recurring Task Schemas ---
class RecurringTaskBase(BaseModel):
    recurrence_pattern: str  # daily, weekly, monthly, yearly
    interval: int = 1
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None


class RecurringTaskCreate(RecurringTaskBase):
    pass


class RecurringTaskRead(RecurringTaskBase):
    id: int
    task_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Attachment Schemas ---
class AttachmentRead(BaseModel):
    id: int
    filename: str
    file_path: str
    content_type: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "normal"  # low, normal, high
    status: str = "pending"  # pending, completed


class TaskCreate(TaskBase):
    category_id: Optional[int] = None
    is_recurring: bool = False
    recurring_rule: Optional[RecurringTaskCreate] = None
    reminders: Optional[List[ReminderBase]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[int] = None
    is_recurring: Optional[bool] = None


class TaskRead(TaskBase):
    id: int
    user_id: int
    category_id: Optional[int] = None
    is_recurring: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryRead] = None
    reminders: List[ReminderRead] = []
    recurring_rules: List[RecurringTaskRead] = []
    attachments: List[AttachmentRead] = []

    model_config = ConfigDict(from_attributes=True)

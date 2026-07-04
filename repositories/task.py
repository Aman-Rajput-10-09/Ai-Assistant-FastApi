from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, update, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.task import Task, RecurringTask, Attachment
from models.category import Category
from models.reminder import Reminder
from repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self):
        super().__init__(Task)

    async def get_task_with_details(self, db: AsyncSession, task_id: int, user_id: int) -> Optional[Task]:
        stmt = (
            select(Task)
            .where(and_(Task.id == task_id, Task.user_id == user_id))
            .options(
                selectinload(Task.category),
                selectinload(Task.reminders),
                selectinload(Task.recurring_rules),
                selectinload(Task.attachments),
            )
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_user_tasks(
        self, db: AsyncSession, user_id: int, *, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[Task]:
        filters = [Task.user_id == user_id]
        if status:
            filters.append(Task.status == status)
            
        stmt = (
            select(Task)
            .where(and_(*filters))
            .options(
                selectinload(Task.category),
                selectinload(Task.reminders),
                selectinload(Task.recurring_rules),
                selectinload(Task.attachments),
            )
            .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_tasks_in_range(
        self, db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[Task]:
        stmt = (
            select(Task)
            .where(
                and_(
                    Task.user_id == user_id,
                    Task.due_date >= start_date,
                    Task.due_date <= end_date
                )
            )
            .options(selectinload(Task.category), selectinload(Task.reminders))
            .order_by(Task.due_date.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def search_by_title_keyword(self, db: AsyncSession, user_id: int, keyword: str) -> List[Task]:
        stmt = (
            select(Task)
            .where(
                and_(
                    Task.user_id == user_id,
                    or_(
                        Task.title.ilike(f"%{keyword}%"),
                        Task.description.ilike(f"%{keyword}%")
                    )
                )
            )
            .options(selectinload(Task.category))
            .limit(20)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def increment_interaction(self, db: AsyncSession, task_id: int) -> None:
        stmt = (
            update(Task)
            .where(Task.id == task_id)
            .values(interaction_count=Task.interaction_count + 1)
        )
        await db.execute(stmt)
        await db.commit()


class CategoryRepository(BaseRepository[Category]):
    def __init__(self):
        super().__init__(Category)

    async def get_by_name(self, db: AsyncSession, user_id: int, name: str) -> Optional[Category]:
        stmt = select(Category).where(
            and_(Category.user_id == user_id, Category.name.ilike(name))
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_or_create(self, db: AsyncSession, user_id: int, name: str, color: Optional[str] = None) -> Category:
        db_obj = await self.get_by_name(db, user_id, name)
        if not db_obj:
            db_obj = Category(user_id=user_id, name=name, color=color)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self):
        super().__init__(Reminder)

    async def get_user_reminders(self, db: AsyncSession, user_id: int) -> List[Reminder]:
        stmt = select(Reminder).where(Reminder.user_id == user_id).order_by(Reminder.reminder_time.asc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_pending_reminders(self, db: AsyncSession, max_time: datetime) -> List[Reminder]:
        stmt = select(Reminder).where(
            and_(Reminder.is_sent == False, Reminder.reminder_time <= max_time)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def mark_as_sent(self, db: AsyncSession, reminder_id: int) -> None:
        stmt = (
            update(Reminder)
            .where(Reminder.id == reminder_id)
            .values(is_sent=True)
        )
        await db.execute(stmt)
        await db.commit()


task_repository = TaskRepository()
category_repository = CategoryRepository()
reminder_repository = ReminderRepository()

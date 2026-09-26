from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from models.task import Task
from models.category import Category


class AnalyticsService:
    async def get_productivity_metrics(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Compile user productivity analytics without using LLM-generated SQL."""
        # 1. Get task status counts
        total_tasks_stmt = select(func.count(Task.id)).where(Task.user_id == user_id)
        completed_tasks_stmt = select(func.count(Task.id)).where(
            and_(Task.user_id == user_id, Task.status == "completed")
        )
        
        total_res = await db.execute(total_tasks_stmt)
        completed_res = await db.execute(completed_tasks_stmt)
        
        total_count = total_res.scalar() or 0
        completed_count = completed_res.scalar() or 0
        pending_count = total_count - completed_count
        
        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0.0
        
        # 2. Get task distribution by category
        category_stmt = (
            select(Category.name, func.count(Task.id))
            .join(Task, Task.category_id == Category.id)
            .where(Task.user_id == user_id)
            .group_by(Category.name)
        )
        cat_res = await db.execute(category_stmt)
        category_distribution = {row[0]: row[1] for row in cat_res.all()}
        
        # 3. Get task counts by priority
        priority_stmt = (
            select(Task.priority, func.count(Task.id))
            .where(Task.user_id == user_id)
            .group_by(Task.priority)
        )
        prio_res = await db.execute(priority_stmt)
        priority_distribution = {row[0]: row[1] for row in prio_res.all()}

        return {
            "total_tasks": total_count,
            "completed_tasks": completed_count,
            "pending_tasks": pending_count,
            "completion_rate": round(completion_rate, 2),
            "category_distribution": category_distribution,
            "priority_distribution": priority_distribution
        }


analytics_service = AnalyticsService()

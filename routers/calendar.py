from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.user import User
from routers.deps import get_current_active_user
from schemas.task import TaskRead
from repositories.task import task_repository

router = APIRouter(prefix="/calendar", tags=["Calendar Queries"])


@router.get("", response_model=List[TaskRead])
async def get_calendar_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve tasks scheduled within a specific timeframe."""
    now = datetime.now(timezone.utc)
    
    # Defaults: Start today, end in 7 days
    actual_start = start_date or now
    actual_end = end_date or (now + timedelta(days=7))
    
    return await task_repository.get_tasks_in_range(db, current_user.id, actual_start, actual_end)

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.user import User
from routers.deps import get_current_active_user
from services.analytics import analytics_service

router = APIRouter(prefix="/analytics", tags=["Productivity Analytics"])


@router.get("")
async def get_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve completion rates, priority distribution, and categorical statistics."""
    metrics = await analytics_service.get_productivity_metrics(db, current_user.id)
    return {"success": True, "metrics": metrics}

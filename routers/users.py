from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.user import User
from routers.deps import get_current_active_user
from schemas.user import UserRead, UserUpdate
from repositories.user import user_repository

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def get_my_profile(current_user: User = Depends(get_current_active_user)):
    """Retrieve the logged in user's profile information."""
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_my_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update profile parameters."""
    return await user_repository.update(db, db_obj=current_user, obj_in=profile_data)

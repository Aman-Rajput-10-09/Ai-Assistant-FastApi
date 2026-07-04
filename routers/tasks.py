from typing import List, Optional
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.user import User
from models.task import Task
from routers.deps import get_current_active_user
from schemas.task import TaskCreate, TaskRead, TaskUpdate, CategoryCreate, CategoryRead
from repositories.task import task_repository, category_repository
from background.worker import background_worker
from core.exceptions import NotFoundException, PermissionDeniedException

router = APIRouter(prefix="/tasks", tags=["Tasks & Scheduling"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a task and trigger async embedding generation."""
    # Resolve category if provided
    category_id = task_in.category_id
    
    # 1. Setup task payload
    task_data = task_in.model_dump(exclude={"recurring_rule", "reminders"})
    task_data["user_id"] = current_user.id
    
    task = await task_repository.create(db, obj_in=task_data)
    
    # 2. Trigger task embedding calculation asynchronously
    background_tasks.add_task(background_worker.generate_task_embedding, task.id)
    
    # Fetch task with category/details
    detailed_task = await task_repository.get_task_with_details(db, task.id, current_user.id)
    return detailed_task


@router.get("", response_model=List[TaskRead])
async def get_tasks(
    task_status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all tasks for the logged in user. Filter by status: pending | completed"""
    return await task_repository.get_user_tasks(db, current_user.id, status=task_status)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task_by_id(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve task details by its database ID."""
    task = await task_repository.get_task_with_details(db, task_id, current_user.id)
    if not task:
        raise NotFoundException(detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update details of a task and regenerate embedding vector in background."""
    task = await task_repository.get(db, task_id)
    if not task or task.user_id != current_user.id:
        raise NotFoundException(detail="Task not found")
        
    updated_task = await task_repository.update(db, db_obj=task, obj_in=task_in)
    
    # Update embedding
    background_tasks.add_task(background_worker.generate_task_embedding, updated_task.id)
    
    return await task_repository.get_task_with_details(db, updated_task.id, current_user.id)


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a task."""
    task = await task_repository.get(db, task_id)
    if not task or task.user_id != current_user.id:
        raise NotFoundException(detail="Task not found")
        
    await task_repository.remove(db, id=task_id)
    return {"message": "Task deleted successfully"}


# --- Categories endpoints ---
@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new task category."""
    obj_data = category_in.model_dump()
    obj_data["user_id"] = current_user.id
    return await category_repository.create(db, obj_in=obj_data)

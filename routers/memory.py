from typing import List
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.user import User
from routers.deps import get_current_active_user
from schemas.chat import ConversationMemoryRead, ConversationMemoryCreate
from repositories.chat import conversation_memory_repository
from rag.embeddings import embedding_service
from background.worker import background_worker

router = APIRouter(prefix="/memory", tags=["Long-Term Memory"])


@router.get("", response_model=List[ConversationMemoryRead])
async def get_memories(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve long-term memory records for the current user."""
    return await conversation_memory_repository.get_user_memories(db, current_user.id)


@router.post("", response_model=ConversationMemoryRead, status_code=status.HTTP_201_CREATED)
async def add_memory_note(
    memory_in: ConversationMemoryCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually insert an item into long-term memory."""
    memory = await conversation_memory_repository.create_memory(
        db,
        user_id=current_user.id,
        conversation="[Manual Entry]",
        summary=memory_in.summary,
        importance_score=memory_in.importance_score
    )
    
    # Schedule embedding generation
    background_tasks.add_task(background_worker.generate_memory_embedding, memory.id)
    
    return memory

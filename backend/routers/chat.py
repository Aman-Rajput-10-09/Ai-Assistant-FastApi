import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.user import User
from routers.deps import get_current_active_user
from schemas.ai import ChatRequest, ChatResponse
from services.intent_router import intent_router_service
from services.db_agent import db_agent_service
from repositories.chat import chat_message_repository
from rag.context_builder import context_builder
from memory.long_term import long_term_memory_service
from llm.gemini import GeminiClient
from background.worker import background_worker

from agents.master_orchestrator import master_orchestrator

router = APIRouter(prefix="/chat", tags=["AI Chat Assistant"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
async def chat_assistant(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Multi-Agent Assistant endpoint that decomposes queries, dispatches sub-tasks 
    to specialized worker agents, and synthesizes consolidated responses.
    """
    user_msg = request.message
    logger.info(f"Received chat message from user {current_user.id}: {user_msg}")
    
    # 1. Save User Message to History
    user_chat_obj = await chat_message_repository.create_chat_message(
        db, user_id=current_user.id, role="user", content=user_msg
    )
    # Schedule embedding generation for user message
    background_tasks.add_task(background_worker.generate_chat_message_embedding, user_chat_obj.id)

    # 2. Process query via Master Orchestrator (Multi-Agent Pipeline)
    response = await master_orchestrator.process_user_message(
        user_query=user_msg,
        db=db,
        user_id=current_user.id,
        background_tasks=background_tasks
    )

    # 3. Save Assistant Response to History
    assistant_chat_obj = await chat_message_repository.create_chat_message(
        db, user_id=current_user.id, role="assistant", content=response.reply
    )
    # Schedule embedding generation for assistant message
    background_tasks.add_task(background_worker.generate_chat_message_embedding, assistant_chat_obj.id)

    # 4. Extract Long-Term Memory from conversation exchange
    background_tasks.add_task(
        long_term_memory_service.extract_and_save_memory,
        db, current_user.id, user_msg, response.reply
    )

    return response


import logging
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
    Intelligent Assistant endpoint that routes requests to SQL DB Agent, 
    Vector Similarity Search, or general conversational RAG.
    """
    user_msg = request.message
    logger.info(f"Received chat message from user {current_user.id}: {user_msg}")
    
    # 1. Route Intent
    intent_output = await intent_router_service.route_intent(user_msg)
    intent = intent_output.intent

    # 2. Save User Message to History
    user_chat_obj = await chat_message_repository.create_chat_message(
        db, user_id=current_user.id, role="user", content=user_msg
    )
    # Schedule embedding generation for user message
    background_tasks.add_task(background_worker.generate_chat_message_embedding, user_chat_obj.id)

    reply_text = ""
    structured_data = None

    # 3. Handle based on Intent Type
    if intent in ["CREATE_TASK", "UPDATE_TASK", "DELETE_TASK", "COMPLETE_TASK", "QUERY_DATABASE", "CALENDAR_QUERY", "ANALYTICS"]:
        # DATABASE AGENT FLOW (SQL CRUD + Analytics + Calendar)
        try:
            # Execute DB operation
            db_res = await db_agent_service.execute_intent(db, current_user.id, intent_output, background_tasks)
            structured_data = db_res
            
            # Use Gemini to generate a friendly response from the database output
            prompt = (
                f"You are a scheduling AI assistant. The user requested: '{user_msg}'.\n"
                f"The database agent executed the action successfully and returned this data:\n"
                f"{db_res}\n\n"
                f"Explain this result clearly and concisely to the user in a natural, polite manner."
            )
            reply_text = await GeminiClient.generate_text(prompt)
        except Exception as e:
            logger.error(f"Database Agent failed: {e}")
            reply_text = f"I encountered an issue processing your request: {str(e)}"
            structured_data = {"error": str(e), "success": False}

    elif intent == "AI_MEMORY":
        # LONG-TERM MEMORY RETRIEVAL / QUERY FLOW
        # Retrieve long-term memory context via vector search
        memory_context = await context_builder.build_context(db, current_user.id, user_msg)
        
        prompt = (
            f"You are a helpful AI assistant with long-term memory capacity.\n"
            f"Here is what you remember about the user:\n"
            f"{memory_context}\n\n"
            f"The user is asking: '{user_msg}'.\n"
            f"Respond to the user utilizing the memory context above if it is relevant. Otherwise, reply conversationally."
        )
        reply_text = await GeminiClient.generate_text(prompt)

    else:
        # GENERAL CHAT FLOW (RAG-Augmented)
        # Compile contextual ranking: recency, importance, semantic similarity, frequency
        rag_context = await context_builder.build_context(db, current_user.id, user_msg)
        
        prompt = (
            f"You are a premium AI scheduling assistant. Here is the relevant context retrieved from the user's account:\n"
            f"{rag_context}\n\n"
            f"User message: '{user_msg}'\n\n"
            f"Please respond to the user query. Reference the context if useful (e.g. reminding them about tasks or info they have set)."
        )
        reply_text = await GeminiClient.generate_text(prompt)

    # 4. Save Assistant Response to History
    assistant_chat_obj = await chat_message_repository.create_chat_message(
        db, user_id=current_user.id, role="assistant", content=reply_text
    )
    # Schedule embedding generation for assistant message
    background_tasks.add_task(background_worker.generate_chat_message_embedding, assistant_chat_obj.id)

    # 5. Extract Long-Term Memory from conversation exchange
    # (If the conversation contains valuable details, index it)
    background_tasks.add_task(
        long_term_memory_service.extract_and_save_memory,
        db, current_user.id, user_msg, reply_text
    )

    return ChatResponse(
        intent=intent,
        reply=reply_text,
        structured_data=structured_data
    )

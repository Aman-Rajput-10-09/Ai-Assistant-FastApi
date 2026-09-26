import logging
from sqlalchemy import select
from core.database import async_session_maker
from models.task import Task
from models.chat import ChatMessage, ConversationMemory
from rag.embeddings import embedding_service
from repositories.task import task_repository
from repositories.chat import chat_message_repository, conversation_memory_repository

logger = logging.getLogger(__name__)


class BackgroundWorker:
    async def generate_task_embedding(self, task_id: int) -> None:
        """Generate and save embedding vector for a given Task ID."""
        logger.info(f"[Background Job] Starting embedding generation for task: {task_id}")
        async with async_session_maker() as db:
            try:
                # Retrieve task with details (e.g. category)
                task = await task_repository.get_task_with_details(db, task_id, task_id)
                # Since get_task_with_details filters by user_id too, let's query directly for background tasks
                stmt = select(Task).where(Task.id == task_id)
                res = await db.execute(stmt)
                task = res.scalars().first()
                
                if not task:
                    logger.error(f"[Background Job] Task {task_id} not found.")
                    return
                
                # Fetch category for formatting if available
                # (due to lazy loading in background session, we load relations explicitly if needed)
                # Let's run task embedding generation
                emb = await embedding_service.get_task_embedding(task)
                
                # Save embedding vector
                task.embedding = emb
                db.add(task)
                await db.commit()
                logger.info(f"[Background Job] Successfully generated embedding for task: {task_id}")
            except Exception as e:
                await db.rollback()
                logger.error(f"[Background Job] Failed task embedding: {e}")

    async def generate_memory_embedding(self, memory_id: int) -> None:
        """Generate and save embedding vector for a given long-term ConversationMemory ID."""
        logger.info(f"[Background Job] Starting embedding generation for memory: {memory_id}")
        async with async_session_maker() as db:
            try:
                stmt = select(ConversationMemory).where(ConversationMemory.id == memory_id)
                res = await db.execute(stmt)
                memory = res.scalars().first()
                
                if not memory:
                    logger.error(f"[Background Job] Memory {memory_id} not found.")
                    return
                
                emb = await embedding_service.get_embedding(memory.summary)
                memory.embedding = emb
                db.add(memory)
                await db.commit()
                logger.info(f"[Background Job] Successfully generated embedding for memory: {memory_id}")
            except Exception as e:
                await db.rollback()
                logger.error(f"[Background Job] Failed memory embedding: {e}")

    async def generate_chat_message_embedding(self, message_id: int) -> None:
        """Generate and save embedding vector for a given ChatMessage ID."""
        logger.info(f"[Background Job] Starting embedding generation for chat message: {message_id}")
        async with async_session_maker() as db:
            try:
                stmt = select(ChatMessage).where(ChatMessage.id == message_id)
                res = await db.execute(stmt)
                message = res.scalars().first()
                
                if not message:
                    logger.error(f"[Background Job] ChatMessage {message_id} not found.")
                    return
                
                emb = await embedding_service.get_chat_message_embedding(message)
                message.embedding = emb
                db.add(message)
                await db.commit()
                logger.info(f"[Background Job] Successfully generated embedding for chat message: {message_id}")
            except Exception as e:
                await db.rollback()
                logger.error(f"[Background Job] Failed chat message embedding: {e}")


background_worker = BackgroundWorker()

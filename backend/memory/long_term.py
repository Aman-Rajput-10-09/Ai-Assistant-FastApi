import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from llm.gemini import GeminiClient
from repositories.chat import conversation_memory_repository
from models.chat import ConversationMemory
from rag.embeddings import embedding_service

logger = logging.getLogger(__name__)


class MemoryExtraction(BaseModel):
    summary: str = Field(
        ..., 
        description="Concise summary of the key user fact. If no new facts, preferences, details, or startup/project ideas are discussed, write 'NONE'."
    )
    importance_score: float = Field(
        ..., 
        description="A float score between 1.0 (very low importance/casual greeting) and 10.0 (high importance like business ideas, health, career, branding names)."
    )


class LongTermMemoryService:
    async def extract_and_save_memory(
        self, db: AsyncSession, user_id: int, user_message: str, assistant_reply: str, background_tasks = None
    ) -> Optional[ConversationMemory]:
        """Analyze dialogue exchange, extract critical user facts, score them, and store them."""
        dialogue = f"User: {user_message}\nAssistant: {assistant_reply}"
        logger.info(f"Analyzing dialogue for long-term memory extraction.")
        
        prompt = (
            f"Extract any important facts, startup ideas, naming preferences, or goals from this dialogue:\n\n"
            f"{dialogue}\n\n"
            f"If there is nothing of substance to remember, write 'NONE' in the summary field."
        )
        
        # 1. Ask Gemini for structured summary & score
        extraction: MemoryExtraction = await GeminiClient.generate_structured_output(
            prompt=prompt,
            schema=MemoryExtraction,
            system_instruction="You are a personal assistant's long-term memory indexing service. Identify information the user shares about themselves that would be helpful to recall later."
        )
        
        if not extraction.summary or extraction.summary.upper() == "NONE":
            logger.info("No significant information detected to save in long-term memory.")
            return None
            
        # 2. Save memory to database (without embedding initially, or generated in background)
        memory = await conversation_memory_repository.create_memory(
            db,
            user_id=user_id,
            conversation=dialogue,
            summary=extraction.summary,
            importance_score=extraction.importance_score
        )
        
        # 3. Schedule embedding generation in background
        if background_tasks:
            from background.worker import background_worker
            background_tasks.add_task(background_worker.generate_memory_embedding, memory.id)
        else:
            # Synchronous fallback if no background worker is configured (e.g. testing)
            emb = await embedding_service.get_embedding(extraction.summary)
            memory.embedding = emb
            db.add(memory)
            await db.commit()
            
        logger.info(f"Memory saved successfully with ID: {memory.id}. Summary: '{extraction.summary}'")
        return memory


long_term_memory_service = LongTermMemoryService()

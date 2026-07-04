from typing import List
from models.task import Task
from models.chat import ChatMessage
from models.reminder import Reminder
from llm.gemini import GeminiClient


class EmbeddingService:
    @staticmethod
    async def get_embedding(text: str) -> List[float]:
        """Generate vector embedding for a raw text."""
        return await GeminiClient.get_embedding(text)

    @classmethod
    async def get_task_embedding(cls, task: Task) -> List[float]:
        """Prepare task text representation and generate embedding."""
        due_str = task.due_date.isoformat() if task.due_date else "None"
        category_str = task.category.name if task.category else "None"
        
        # Build textual representation
        text_repr = (
            f"Task Title: {task.title}\n"
            f"Description: {task.description or 'No description'}\n"
            f"Priority: {task.priority}\n"
            f"Status: {task.status}\n"
            f"Category: {category_str}\n"
            f"Due Date: {due_str}"
        )
        return await cls.get_embedding(text_repr)

    @classmethod
    async def get_chat_message_embedding(cls, message: ChatMessage) -> List[float]:
        """Prepare chat message text representation and generate embedding."""
        text_repr = f"Role: {message.role}\nContent: {message.content}"
        return await cls.get_embedding(text_repr)


embedding_service = EmbeddingService()

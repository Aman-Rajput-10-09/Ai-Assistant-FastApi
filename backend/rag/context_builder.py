import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from models.task import Task
from models.chat import ChatMessage, ConversationMemory
from rag.retrieval import retrieval_service


class ContextBuilder:
    def __init__(
        self,
        weight_sim: float = 0.5,
        weight_rec: float = 0.2,
        weight_imp: float = 0.2,
        weight_freq: float = 0.1,
        recency_decay_days: float = 0.05,  # e^(-decay * days)
        token_char_limit: int = 4000
    ):
        self.w_sim = weight_sim
        self.w_rec = weight_rec
        self.w_imp = weight_imp
        self.w_freq = weight_freq
        self.decay_days = recency_decay_days
        self.token_char_limit = token_char_limit

    async def build_context(self, db: AsyncSession, user_id: int, query: str) -> str:
        """Retrieve, rank, and format relevant context from Tasks, Messages, and Memories."""
        # 1. Retrieve raw candidates
        tasks_raw = await retrieval_service.retrieve_similar_tasks(db, user_id, query, limit=5)
        messages_raw = await retrieval_service.retrieve_similar_messages(db, user_id, query, limit=5)
        memories_raw = await retrieval_service.retrieve_similar_memories(db, user_id, query, limit=5)
        
        candidates: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        
        # 2. Score Tasks
        for task, distance in tasks_raw:
            similarity = 1.0 - distance
            
            # Recency
            days_old = (now - task.created_at).days
            recency = math.exp(-self.decay_days * max(0, days_old))
            
            # Importance
            prio_map = {"low": 0.3, "normal": 0.6, "high": 1.0}
            importance = prio_map.get(task.priority.lower(), 0.6)
            
            # Frequency (interaction count)
            freq = 1.0 - math.exp(-0.2 * task.interaction_count)
            
            score = (
                self.w_sim * similarity +
                self.w_rec * recency +
                self.w_imp * importance +
                self.w_freq * freq
            )
            
            repr_str = (
                f"[Task] Title: '{task.title}' | Status: {task.status} | "
                f"Due: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'None'} | "
                f"Priority: {task.priority}"
            )
            
            candidates.append({"score": score, "text": repr_str, "type": "task"})

        # 3. Score Messages
        for msg, distance in messages_raw:
            similarity = 1.0 - distance
            
            # Recency
            days_old = (now - msg.created_at).days
            recency = math.exp(-self.decay_days * max(0, days_old))
            
            # Importance
            importance = 0.5
            
            # Frequency
            freq = 0.0
            
            score = (
                self.w_sim * similarity +
                self.w_rec * recency +
                self.w_imp * importance +
                self.w_freq * freq
            )
            
            repr_str = f"[Chat History] {msg.role.capitalize()}: {msg.content}"
            candidates.append({"score": score, "text": repr_str, "type": "message"})

        # 4. Score Memories
        for memory, distance in memories_raw:
            similarity = 1.0 - distance
            
            # Recency
            days_old = (now - memory.created_at).days
            recency = math.exp(-self.decay_days * max(0, days_old))
            
            # Importance (importance score is scale of 1 to 10)
            importance = max(1.0, min(10.0, memory.importance_score)) / 10.0
            
            # Frequency
            freq = 0.0
            
            score = (
                self.w_sim * similarity +
                self.w_rec * recency +
                self.w_imp * importance +
                self.w_freq * freq
            )
            
            repr_str = f"[Memory Summary] {memory.summary}"
            candidates.append({"score": score, "text": repr_str, "type": "memory"})

        # 5. Rank candidates by final combined score
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # 6. Assemble context within token character budget
        context_parts = []
        current_len = 0
        
        for cand in candidates:
            cand_text = f"- {cand['text']}\n"
            if current_len + len(cand_text) > self.token_char_limit:
                break
            context_parts.append(cand_text)
            current_len += len(cand_text)

        if not context_parts:
            return "No matching context found."
            
        return "".join(context_parts)


context_builder = ContextBuilder()

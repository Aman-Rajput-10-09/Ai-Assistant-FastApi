from typing import List, Tuple, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models.task import Task
from models.chat import ChatMessage, ConversationMemory
from rag.embeddings import embedding_service


class RetrievalService:
    async def retrieve_similar_tasks(
        self, db: AsyncSession, user_id: int, query: str, limit: int = 5
    ) -> List[Tuple[Task, float]]:
        """Find tasks similar to query using pgvector cosine distance."""
        query_emb = await embedding_service.get_embedding(query)
        
        # Calculate cosine distance using .cosine_distance()
        stmt = (
            select(Task)
            .where(and_(Task.user_id == user_id, Task.embedding.isnot(None)))
            .order_by(Task.embedding.cosine_distance(query_emb))
            .limit(limit)
        )
        
        res = await db.execute(stmt)
        tasks = res.scalars().all()
        
        # Calculate similarity score: 1.0 - cosine_distance
        results = []
        for t in tasks:
            # We can re-fetch distance in SQL or compute in python, but let's fetch in query to be exact.
            # However, selecting the entity along with the distance is cleaner:
            # select(Task, Task.embedding.cosine_distance(query_emb))
            # Let's perform a query that returns both the task and distance.
            pass
            
        # Let's write the query that returns both Task and the distance
        distance_expr = Task.embedding.cosine_distance(query_emb)
        stmt_with_dist = (
            select(Task, distance_expr)
            .where(and_(Task.user_id == user_id, Task.embedding.isnot(None)))
            .order_by(distance_expr)
            .limit(limit)
        )
        res_with_dist = await db.execute(stmt_with_dist)
        return [(row[0], float(row[1])) for row in res_with_dist.all()]

    async def retrieve_similar_messages(
        self, db: AsyncSession, user_id: int, query: str, limit: int = 5
    ) -> List[Tuple[ChatMessage, float]]:
        """Find chat messages similar to query using pgvector cosine distance."""
        query_emb = await embedding_service.get_embedding(query)
        distance_expr = ChatMessage.embedding.cosine_distance(query_emb)
        
        stmt = (
            select(ChatMessage, distance_expr)
            .where(and_(ChatMessage.user_id == user_id, ChatMessage.embedding.isnot(None)))
            .order_by(distance_expr)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return [(row[0], float(row[1])) for row in res.all()]

    async def retrieve_similar_memories(
        self, db: AsyncSession, user_id: int, query: str, limit: int = 5
    ) -> List[Tuple[ConversationMemory, float]]:
        """Find long-term memories similar to query using pgvector cosine distance."""
        query_emb = await embedding_service.get_embedding(query)
        distance_expr = ConversationMemory.embedding.cosine_distance(query_emb)
        
        stmt = (
            select(ConversationMemory, distance_expr)
            .where(and_(ConversationMemory.user_id == user_id, ConversationMemory.embedding.isnot(None)))
            .order_by(distance_expr)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return [(row[0], float(row[1])) for row in res.all()]


retrieval_service = RetrievalService()

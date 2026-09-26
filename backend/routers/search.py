from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.user import User
from routers.deps import get_current_active_user
from schemas.ai import SearchRequest, SearchResponse, SearchResultItem
from rag.retrieval import retrieval_service

router = APIRouter(prefix="/search", tags=["Semantic Search"])


@router.post("", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Semantic vector search across tasks, chat messages, and long-term memory."""
    query = request.query
    limit = request.limit
    
    # 1. Query PGVector similarities
    tasks = await retrieval_service.retrieve_similar_tasks(db, current_user.id, query, limit=limit)
    messages = await retrieval_service.retrieve_similar_messages(db, current_user.id, query, limit=limit)
    memories = await retrieval_service.retrieve_similar_memories(db, current_user.id, query, limit=limit)
    
    results = []
    
    # Map tasks
    for task, distance in tasks:
        similarity = round(1.0 - distance, 4)
        results.append(
            SearchResultItem(
                type="task",
                id=task.id,
                title=task.title,
                description=task.description,
                similarity=similarity,
                timestamp=task.created_at
            )
        )
        
    # Map messages
    for msg, distance in messages:
        similarity = round(1.0 - distance, 4)
        results.append(
            SearchResultItem(
                type="chat_history",
                id=msg.id,
                title=f"Chat ({msg.role})",
                description=msg.content,
                similarity=similarity,
                timestamp=msg.created_at
            )
        )
        
    # Map memories
    for memory, distance in memories:
        similarity = round(1.0 - distance, 4)
        results.append(
            SearchResultItem(
                type="memory",
                id=memory.id,
                title="AI Long-Term Memory Summary",
                description=memory.summary,
                similarity=similarity,
                timestamp=memory.created_at
            )
        )

    # Sort results overall by similarity score
    results.sort(key=lambda x: x.similarity, reverse=True)
    
    return SearchResponse(
        query=query,
        results=results[:limit] # return top K overall matches
    )

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# --- Intent Router Output ---
class IntentRouterOutput(BaseModel):
    intent: str = Field(
        ..., 
        description="Must be one of: CREATE_TASK, UPDATE_TASK, DELETE_TASK, COMPLETE_TASK, QUERY_DATABASE, CALENDAR_QUERY, ANALYTICS, AI_MEMORY, GENERAL_CHAT"
    )
    # Parameters for CREATE_TASK / UPDATE_TASK
    title: Optional[str] = Field(None, description="Title of the task to create/update")
    description: Optional[str] = Field(None, description="Detailed description of the task")
    due_date: Optional[str] = Field(None, description="ISO-formatted due date-time for the task (e.g. 2026-07-05T20:00:00)")
    priority: Optional[str] = Field(None, description="Priority level: low, normal, or high")
    category: Optional[str] = Field(None, description="Category name (e.g. Work, Personal, Fitness)")
    
    # Parameters for UPDATE_TASK / DELETE_TASK / COMPLETE_TASK
    task_search_query: Optional[str] = Field(None, description="Keywords or details to find the target task to modify/complete/delete")
    
    # Parameters for QUERY_DATABASE / CALENDAR_QUERY / ANALYTICS
    sql_search_filter: Optional[str] = Field(None, description="Plain text filters for task searching, e.g. tasks from tomorrow, or meetings with Rahul")
    time_frame_start: Optional[str] = Field(None, description="ISO datetime start range for calendar queries")
    time_frame_end: Optional[str] = Field(None, description="ISO datetime end range for calendar queries")
    analytics_metric: Optional[str] = Field(None, description="Type of metric desired: completion_rate, task_count, category_distribution")
    
    # Parameters for GENERAL_CHAT / AI_MEMORY
    chat_reply_suggestion: Optional[str] = Field(None, description="Draft answer if GENERAL_CHAT or simple clarification needed")


# --- Chat Request and Response ---
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    intent: str
    reply: str
    structured_data: Optional[Dict[str, Any]] = None


# --- Semantic Search Schemas ---
class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class SearchResultItem(BaseModel):
    type: str  # task, message, memory, reminder
    id: int
    title: str
    description: Optional[str] = None
    similarity: float
    timestamp: datetime


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]

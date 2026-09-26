import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from agents.base import BaseWorkerAgent
from schemas.ai import SubTask, SubTaskResult
from rag.context_builder import context_builder

logger = logging.getLogger(__name__)


class MemoryWorkerAgent(BaseWorkerAgent):
    agent_name = "memory_worker"

    async def execute(
        self,
        sub_task: SubTask,
        db: AsyncSession,
        user_id: int,
        background_tasks: Optional[Any] = None
    ) -> SubTaskResult:
        logger.info(f"[MemoryWorkerAgent] Executing sub-task {sub_task.task_id} for user {user_id}")
        query = sub_task.sub_prompt or sub_task.task_search_query or "user facts and history"
        try:
            memory_context = await context_builder.build_context(db, user_id, query)
            return SubTaskResult(
                task_id=sub_task.task_id,
                intent=sub_task.intent,
                agent_target=self.agent_name,
                success=True,
                output_data={"memory_context": memory_context},
                summary_text="Retrieved long-term memory context"
            )
        except Exception as e:
            logger.error(f"[MemoryWorkerAgent] Sub-task {sub_task.task_id} failed: {e}")
            return SubTaskResult(
                task_id=sub_task.task_id,
                intent=sub_task.intent,
                agent_target=self.agent_name,
                success=False,
                output_data={"error": str(e)},
                summary_text=f"Failed to retrieve memory context: {str(e)}"
            )


memory_worker_agent = MemoryWorkerAgent()

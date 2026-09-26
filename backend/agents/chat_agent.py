import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from agents.base import BaseWorkerAgent
from schemas.ai import SubTask, SubTaskResult
from rag.context_builder import context_builder

logger = logging.getLogger(__name__)


class GeneralChatWorkerAgent(BaseWorkerAgent):
    agent_name = "chat_worker"

    async def execute(
        self,
        sub_task: SubTask,
        db: AsyncSession,
        user_id: int,
        background_tasks: Optional[Any] = None
    ) -> SubTaskResult:
        logger.info(f"[GeneralChatWorkerAgent] Executing sub-task {sub_task.task_id} for user {user_id}")
        query = sub_task.sub_prompt or "general conversation"
        try:
            rag_context = await context_builder.build_context(db, user_id, query)
            return SubTaskResult(
                task_id=sub_task.task_id,
                intent=sub_task.intent,
                agent_target=self.agent_name,
                success=True,
                output_data={"rag_context": rag_context, "sub_prompt": query},
                summary_text="Gathered conversational context"
            )
        except Exception as e:
            logger.error(f"[GeneralChatWorkerAgent] Sub-task {sub_task.task_id} failed: {e}")
            return SubTaskResult(
                task_id=sub_task.task_id,
                intent=sub_task.intent,
                agent_target=self.agent_name,
                success=False,
                output_data={"error": str(e), "sub_prompt": query},
                summary_text=f"Failed to gather conversational context: {str(e)}"
            )


chat_worker_agent = GeneralChatWorkerAgent()

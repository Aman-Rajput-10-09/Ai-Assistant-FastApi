import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from agents.base import BaseWorkerAgent
from schemas.ai import SubTask, SubTaskResult
from services.analytics import analytics_service

logger = logging.getLogger(__name__)


class AnalyticsWorkerAgent(BaseWorkerAgent):
    agent_name = "analytics_worker"

    async def execute(
        self,
        sub_task: SubTask,
        db: AsyncSession,
        user_id: int,
        background_tasks: Optional[Any] = None
    ) -> SubTaskResult:
        logger.info(f"[AnalyticsWorkerAgent] Executing sub-task {sub_task.task_id} for user {user_id}")
        try:
            metrics = await analytics_service.get_productivity_metrics(db, user_id)
            return SubTaskResult(
                task_id=sub_task.task_id,
                intent=sub_task.intent,
                agent_target=self.agent_name,
                success=True,
                output_data={"metrics": metrics},
                summary_text="Productivity metrics compiled successfully"
            )
        except Exception as e:
            logger.error(f"[AnalyticsWorkerAgent] Sub-task {sub_task.task_id} failed: {e}")
            return SubTaskResult(
                task_id=sub_task.task_id,
                intent=sub_task.intent,
                agent_target=self.agent_name,
                success=False,
                output_data={"error": str(e)},
                summary_text=f"Failed to compile analytics: {str(e)}"
            )


analytics_worker_agent = AnalyticsWorkerAgent()

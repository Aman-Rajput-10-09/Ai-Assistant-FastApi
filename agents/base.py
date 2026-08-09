import abc
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.ai import SubTask, SubTaskResult


class BaseWorkerAgent(abc.ABC):
    agent_name: str

    @abc.abstractmethod
    async def execute(
        self,
        sub_task: SubTask,
        db: AsyncSession,
        user_id: int,
        background_tasks: Optional[Any] = None
    ) -> SubTaskResult:
        """Execute the sub-task assigned to this specialized worker agent."""
        pass

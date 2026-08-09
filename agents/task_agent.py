import logging
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from agents.base import BaseWorkerAgent
from schemas.ai import SubTask, SubTaskResult, IntentRouterOutput
from services.db_agent import db_agent_service
from services.intent_router import normalize_due_date, LOCAL_TZ

logger = logging.getLogger(__name__)


def _format_alarm_fields(reminder_at: Optional[str]) -> dict:
    if not reminder_at:
        return {
            "should_schedule_alarm": False,
            "reminder_at": None,
            "reminder_date": None,
            "reminder_time": None,
        }

    try:
        parsed = datetime.fromisoformat(reminder_at)
    except ValueError:
        return {
            "should_schedule_alarm": False,
            "reminder_at": None,
            "reminder_date": None,
            "reminder_time": None,
        }

    return {
        "should_schedule_alarm": True,
        "reminder_at": parsed.isoformat(),
        "reminder_date": parsed.date().isoformat(),
        "reminder_time": parsed.strftime("%H:%M"),
    }


class TaskWorkerAgent(BaseWorkerAgent):
    agent_name = "task_worker"

    async def execute(
        self,
        sub_task: SubTask,
        db: AsyncSession,
        user_id: int,
        background_tasks: Optional[Any] = None
    ) -> SubTaskResult:
        logger.info(f"[TaskWorkerAgent] Executing sub-task {sub_task.task_id} ({sub_task.intent}) for user {user_id}")

        # Normalize due date if provided or if task creation/update requires it
        due_date = sub_task.due_date
        if sub_task.intent in {"CREATE_TASK", "UPDATE_TASK"} and (due_date or sub_task.title):
            due_date = normalize_due_date(sub_task.sub_prompt or sub_task.title or "", due_date, datetime.now(LOCAL_TZ))

        # Convert SubTask to IntentRouterOutput for db_agent_service compatibility
        router_output = IntentRouterOutput(
            intent=sub_task.intent,
            title=sub_task.title,
            description=sub_task.description,
            due_date=due_date,
            priority=sub_task.priority,
            category=sub_task.category,
            task_search_query=sub_task.task_search_query,
            sql_search_filter=sub_task.sql_search_filter,
            time_frame_start=sub_task.time_frame_start,
            time_frame_end=sub_task.time_frame_end,
            analytics_metric=sub_task.analytics_metric
        )

        try:
            db_res = await db_agent_service.execute_intent(db, user_id, router_output, background_tasks)

            alarm_fields = {
                "should_schedule_alarm": False,
                "reminder_at": None,
                "reminder_date": None,
                "reminder_time": None,
            }
            if sub_task.intent in {"CREATE_TASK", "UPDATE_TASK"} and db_res.get("success") and due_date:
                alarm_fields = _format_alarm_fields(due_date)

            return SubTaskResult(
                task_id=sub_task.task_id,
                intent=sub_task.intent,
                agent_target=self.agent_name,
                success=db_res.get("success", True),
                output_data=db_res,
                summary_text=db_res.get("message", "Task operation completed"),
                should_schedule_alarm=alarm_fields["should_schedule_alarm"],
                reminder_at=alarm_fields["reminder_at"],
                reminder_date=alarm_fields["reminder_date"],
                reminder_time=alarm_fields["reminder_time"]
            )
        except Exception as e:
            logger.error(f"[TaskWorkerAgent] Sub-task {sub_task.task_id} failed: {e}")
            return SubTaskResult(
                task_id=sub_task.task_id,
                intent=sub_task.intent,
                agent_target=self.agent_name,
                success=False,
                output_data={"error": str(e)},
                summary_text=f"Failed to execute task operation: {str(e)}"
            )


task_worker_agent = TaskWorkerAgent()

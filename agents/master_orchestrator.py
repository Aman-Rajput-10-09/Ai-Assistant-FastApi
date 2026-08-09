import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from llm.gemini import GeminiClient
from schemas.ai import MultiAgentPlan, SubTask, SubTaskResult, ChatResponse
from agents.task_agent import task_worker_agent
from agents.analytics_agent import analytics_worker_agent
from agents.memory_agent import memory_worker_agent
from agents.chat_agent import chat_worker_agent

logger = logging.getLogger(__name__)
LOCAL_TZ = ZoneInfo("Asia/Kolkata")


def _build_orchestrator_system_instruction(now: datetime) -> str:
    return f"""
You are the Master Orchestrator Agent for an intelligent scheduling assistant.
Your job is to analyze the user's natural language request and decompose it into one or more sub-tasks assigned to specialized worker agents.

Current Local Time: {now.isoformat()}

Available Worker Agents and Intents:
1. task_worker:
   - CREATE_TASK: Create a task, reminder, todo, event, or meeting. (Always extract `due_date`, `title`, `priority`, `category`).
   - UPDATE_TASK: Modify or reschedule an existing task. (Extract `task_search_query`, `title`, `due_date`).
   - DELETE_TASK: Remove a task. (Extract `task_search_query`).
   - COMPLETE_TASK: Mark a task as finished. (Extract `task_search_query`).
   - QUERY_DATABASE: Search tasks/reminders/notes. (Extract `sql_search_filter`).
   - CALENDAR_QUERY: Agenda or schedule queries for specific days/timeframes. (Extract `time_frame_start`, `time_frame_end`, `sql_search_filter`).

2. analytics_worker:
   - ANALYTICS: Productivity stats, task completion rates, metrics, category performance. (Extract `analytics_metric`).

3. memory_worker:
   - AI_MEMORY: Personal user facts, core goals, preferences, or queries about what the assistant remembers. (Extract `sub_prompt`).

4. chat_worker:
   - GENERAL_CHAT: Conversational questions, general knowledge, or chit-chat. (Extract `sub_prompt`).

Instructions:
- If the user query contains MULTIPLE distinct actions (e.g., "Create a task to call John tomorrow AND show my productivity stats AND check today's schedule"), set `is_multi_intent: true` and create a sub-task for EACH action in `sub_tasks`.
- If the user query contains a SINGLE action, set `is_multi_intent: false` and create 1 sub-task in `sub_tasks`.
- Assign `task_id` sequentially: `task_1`, `task_2`, etc.
- Provide accurate parameters for dates/times relative to current local time {now.isoformat()}.
"""


class MasterOrchestrator:
    def __init__(self):
        self.worker_agents = {
            "task_worker": task_worker_agent,
            "analytics_worker": analytics_worker_agent,
            "memory_worker": memory_worker_agent,
            "chat_worker": chat_worker_agent,
        }

    async def decompose_query(self, user_query: str) -> MultiAgentPlan:
        """Use LLM to decompose the user query into a MultiAgentPlan containing sub-tasks."""
        now = datetime.now(LOCAL_TZ)
        prompt = f"Decompose this user query into sub-tasks: '{user_query}'"

        plan = await GeminiClient.generate_structured_output(
            prompt=prompt,
            schema=MultiAgentPlan,
            system_instruction=_build_orchestrator_system_instruction(now)
        )
        plan.user_query = user_query
        return plan

    async def execute_plan(
        self,
        plan: MultiAgentPlan,
        db: AsyncSession,
        user_id: int,
        background_tasks: Optional[Any] = None
    ) -> List[SubTaskResult]:
        """Dispatch each sub-task in the plan to its designated worker agent."""
        results: List[SubTaskResult] = []

        for sub_task in plan.sub_tasks:
            agent = self.worker_agents.get(sub_task.agent_target, chat_worker_agent)
            result = await agent.execute(sub_task, db, user_id, background_tasks)
            results.append(result)

        return results

    async def synthesize_response(self, user_query: str, plan: MultiAgentPlan, results: List[SubTaskResult]) -> str:
        """Combine all sub-task results into a single cohesive, polite user response."""
        results_summary = []
        for r in results:
            results_summary.append(
                f"- [Sub-task {r.task_id} ({r.intent} via {r.agent_target})]: Success={r.success}\n"
                f"  Summary: {r.summary_text}\n"
                f"  Details: {r.output_data}"
            )

        combined_summary = "\n".join(results_summary)

        synthesis_prompt = (
            f"You are an intelligent scheduling AI assistant.\n"
            f"The user submitted the following request: '{user_query}'\n\n"
            f"The request was processed by multiple specialized sub-agents with the following execution results:\n"
            f"{combined_summary}\n\n"
            f"Please synthesize a single, natural, polite, and cohesive response that clearly answers all parts of the user's request. "
            f"Do not mention internal technical terms like sub-agents or JSON structures."
        )

        return await GeminiClient.generate_text(synthesis_prompt)

    async def process_user_message(
        self,
        user_query: str,
        db: AsyncSession,
        user_id: int,
        background_tasks: Optional[Any] = None
    ) -> ChatResponse:
        """Full pipeline: Decompose -> Execute Sub-tasks -> Synthesize Output."""
        logger.info(f"[MasterOrchestrator] Processing user message: '{user_query}'")

        # 1. Decompose query into sub-tasks
        plan = await self.decompose_query(user_query)
        logger.info(f"[MasterOrchestrator] Multi-intent plan (is_multi={plan.is_multi_intent}): {len(plan.sub_tasks)} sub-tasks generated")

        # Fallback if no subtasks generated
        if not plan.sub_tasks:
            fallback_subtask = SubTask(
                task_id="task_1",
                intent="GENERAL_CHAT",
                agent_target="chat_worker",
                sub_prompt=user_query
            )
            plan.sub_tasks = [fallback_subtask]

        # 2. Execute all sub-tasks via specialized worker agents
        results = await self.execute_plan(plan, db, user_id, background_tasks)

        # 3. Consolidate results metadata (intents, alarm directives, structured data)
        intents_list = [r.intent for r in results]
        combined_intent = f"MULTI_AGENT [{', '.join(intents_list)}]" if plan.is_multi_intent and len(intents_list) > 1 else intents_list[0]

        should_schedule_alarm = False
        reminder_at = None
        reminder_date = None
        reminder_time = None
        combined_structured_data: Dict[str, Any] = {}
        executed_subtasks_log: List[Dict[str, Any]] = []

        for r in results:
            executed_subtasks_log.append({
                "task_id": r.task_id,
                "intent": r.intent,
                "agent_target": r.agent_target,
                "success": r.success,
                "summary": r.summary_text,
                "data": r.output_data
            })
            if r.output_data:
                combined_structured_data[r.task_id] = r.output_data
            if r.should_schedule_alarm:
                should_schedule_alarm = True
                reminder_at = r.reminder_at
                reminder_date = r.reminder_date
                reminder_time = r.reminder_time

        # 4. Synthesize final response using LLM
        reply_text = await self.synthesize_response(user_query, plan, results)

        return ChatResponse(
            intent=combined_intent,
            reply=reply_text,
            structured_data=combined_structured_data,
            should_schedule_alarm=should_schedule_alarm,
            reminder_at=reminder_at,
            reminder_date=reminder_date,
            reminder_time=reminder_time,
            executed_subtasks=executed_subtasks_log
        )


master_orchestrator = MasterOrchestrator()

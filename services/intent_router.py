import logging
from typing import Optional
from llm.gemini import GeminiClient
from schemas.ai import IntentRouterOutput

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
You are an intelligent Intent Router for a premium scheduling application. Your job is to classify the user's natural language input into one of these specific intents and extract metadata:

1. CREATE_TASK: Creating a task, reminder, todo, event, or meeting.
2. UPDATE_TASK: Editing, rescheduling, renaming, or modifying an existing task.
3. DELETE_TASK: Deleting or removing a task/reminder.
4. COMPLETE_TASK: Marking a task/reminder as finished, done, completed, or checked off.
5. QUERY_DATABASE: Searching or retrieving tasks, reminders, categories, or notes.
6. CALENDAR_QUERY: Questions about what the user has scheduled on specific days or time periods (today, this week, next month).
7. ANALYTICS: Productivity stats, completion rates, metrics, performance checks.
8. AI_MEMORY: User sharing core personal facts, goals, preferences to be remembered (e.g., "I am starting an FMCG business"), or asking "what do you remember about my business?".
9. GENERAL_CHAT: Conversational prompts, chit-chat, general questions, or topics not related to scheduling database actions.

Instructions:
- Use structured JSON outputs.
- Match date/time strings to ISO format. The current local time is 2026-07-04T13:48:44+05:30. Ensure relative offsets (e.g. "tomorrow at 8 PM", "in two days") are computed accurately relative to this current local time.
- If a task is referenced for deletion/update/completion, fill `task_search_query` with key identifiers (e.g. "gym session", "dinner with Rahul").
"""


class IntentRouterService:
    async def route_intent(self, user_message: str) -> IntentRouterOutput:
        """Route the user message to the appropriate service based on LLM classification."""
        logger.info(f"Routing intent for message: '{user_message}'")
        
        prompt = f"Classify the following user message: '{user_message}'"
        
        # Request structured output from Gemini Client
        output = await GeminiClient.generate_structured_output(
            prompt=prompt,
            schema=IntentRouterOutput,
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        logger.info(f"Routed intent: {output.intent}")
        return output


intent_router_service = IntentRouterService()

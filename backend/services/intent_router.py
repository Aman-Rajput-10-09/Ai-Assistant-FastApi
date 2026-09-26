import logging
import re
from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
from llm.gemini import GeminiClient
from schemas.ai import IntentRouterOutput

logger = logging.getLogger(__name__)

LOCAL_TZ = ZoneInfo("Asia/Kolkata")
DEFAULT_REMINDER_TIME = time(hour=9, minute=0)

DATE_PATTERN = re.compile(
    r"\b(today|tomorrow|tonight|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
    r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b",
    re.IGNORECASE,
)
TIME_PATTERN = re.compile(
    r"\b(\d{1,2}:\d{2}\s*(?:am|pm)?|\d{1,2}\s*(?:am|pm)|noon|midnight)\b",
    re.IGNORECASE,
)


def _build_system_instruction(now: datetime) -> str:
    return f"""
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
- Match date/time strings to ISO format. The current local time is {now.isoformat()}. Ensure relative offsets (e.g. "tomorrow at 8 PM", "in two days") are computed accurately relative to this current local time.
- For CREATE_TASK reminder/task requests, always provide `due_date`.
- If the user gives a date but no time, use the default reminder time 09:00.
- If the user gives a time but no date, use today's date if that time is still upcoming; otherwise use tomorrow's date.
- If the user gives neither date nor time, use today's date at 09:00 if that time is still upcoming; otherwise use tomorrow at 09:00.
- If a task is referenced for deletion/update/completion, fill `task_search_query` with key identifiers (e.g. "gym session", "dinner with Rahul").
"""


def _parse_due_date(due_date: Optional[str]) -> Optional[datetime]:
    if not due_date:
        return None

    try:
        parsed = datetime.fromisoformat(due_date)
    except ValueError:
        logger.warning(f"Could not parse routed due date: {due_date}")
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LOCAL_TZ)
    return parsed.astimezone(LOCAL_TZ)


def _default_reminder_datetime(now: datetime) -> datetime:
    candidate = datetime.combine(now.date(), DEFAULT_REMINDER_TIME, tzinfo=LOCAL_TZ)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def _extract_time_from_message(message: str) -> Optional[time]:
    match = TIME_PATTERN.search(message)
    if not match:
        return None

    raw_time = match.group(1).lower().replace(" ", "")
    if raw_time == "noon":
        return time(hour=12, minute=0)
    if raw_time == "midnight":
        return time(hour=0, minute=0)

    meridiem = None
    if raw_time.endswith("am") or raw_time.endswith("pm"):
        meridiem = raw_time[-2:]
        raw_time = raw_time[:-2]

    if ":" in raw_time:
        hour_text, minute_text = raw_time.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    else:
        hour = int(raw_time)
        minute = 0

    if meridiem == "am" and hour == 12:
        hour = 0
    elif meridiem == "pm" and hour != 12:
        hour += 12

    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return None
    return time(hour=hour, minute=minute)


def _extract_date_from_message(message: str, now: datetime) -> Optional[date]:
    lower_message = message.lower()
    if "tomorrow" in lower_message:
        return now.date() + timedelta(days=1)
    if "today" in lower_message or "tonight" in lower_message:
        return now.date()

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    for weekday_name, weekday_index in weekdays.items():
        if re.search(rf"\b{weekday_name}\b", lower_message):
            days_ahead = (weekday_index - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return now.date() + timedelta(days=days_ahead)

    return None


def normalize_due_date(user_message: str, due_date: Optional[str], now: Optional[datetime] = None) -> str:
    """Apply deterministic reminder defaults after the LLM extracts intent metadata."""
    local_now = (now or datetime.now(LOCAL_TZ)).astimezone(LOCAL_TZ)
    message = user_message.lower()
    has_date = bool(DATE_PATTERN.search(message))
    has_time = bool(TIME_PATTERN.search(message))

    parsed_due_date = _parse_due_date(due_date)

    explicit_time = _extract_time_from_message(message)
    if explicit_time:
        explicit_date = _extract_date_from_message(message, local_now)
        if explicit_date is None and has_date and parsed_due_date:
            explicit_date = parsed_due_date.date()
        if explicit_date is None:
            today_candidate = datetime.combine(local_now.date(), explicit_time, tzinfo=LOCAL_TZ)
            explicit_date = today_candidate.date() if today_candidate > local_now else today_candidate.date() + timedelta(days=1)

        return datetime.combine(explicit_date, explicit_time, tzinfo=LOCAL_TZ).isoformat()

    if parsed_due_date is None:
        return _default_reminder_datetime(local_now).isoformat()

    normalized = parsed_due_date

    if not has_time:
        normalized = normalized.replace(
            hour=DEFAULT_REMINDER_TIME.hour,
            minute=DEFAULT_REMINDER_TIME.minute,
            second=0,
            microsecond=0,
        )

    if not has_date:
        today_candidate = datetime.combine(local_now.date(), normalized.timetz())
        today_candidate = today_candidate.astimezone(LOCAL_TZ)
        normalized = today_candidate if today_candidate > local_now else today_candidate + timedelta(days=1)

    return normalized.isoformat()


class IntentRouterService:
    async def route_intent(self, user_message: str) -> IntentRouterOutput:
        """Route the user message to the appropriate service based on LLM classification."""
        logger.info(f"Routing intent for message: '{user_message}'")
        
        prompt = f"Classify the following user message: '{user_message}'"
        now = datetime.now(LOCAL_TZ)
        
        # Request structured output from Gemini Client
        output = await GeminiClient.generate_structured_output(
            prompt=prompt,
            schema=IntentRouterOutput,
            system_instruction=_build_system_instruction(now)
        )

        if output.intent == "CREATE_TASK" or (output.intent == "UPDATE_TASK" and output.due_date):
            output.due_date = normalize_due_date(user_message, output.due_date, now)
        
        logger.info(f"Routed intent: {output.intent}")
        return output


intent_router_service = IntentRouterService()

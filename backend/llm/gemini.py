import logging
import json
import random
from typing import Any, List, Optional, Type, TypeVar

try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    _USE_GENAI_SDK = True
except Exception:
    google_genai = None
    genai_types = None
    _USE_GENAI_SDK = False

if _USE_GENAI_SDK:
    legacy_genai = None
    _USE_LEGACY_SDK = False
else:
    try:
        import google.generativeai as legacy_genai
        _USE_LEGACY_SDK = True
    except Exception:
        legacy_genai = None
        _USE_LEGACY_SDK = False

from pydantic import BaseModel
from core.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini API if key is available
is_gemini_active = False
_genai_client = None
if settings.GEMINI_API_KEY:
    try:
        if _USE_GENAI_SDK:
            _genai_client = google_genai.Client(api_key=settings.GEMINI_API_KEY)
            is_gemini_active = True
            logger.info("Gemini API initialized with google-genai SDK.")
        elif _USE_LEGACY_SDK:
            legacy_genai.configure(api_key=settings.GEMINI_API_KEY)
            is_gemini_active = True
            logger.info("Gemini API initialized with legacy google-generativeai SDK.")
        else:
            logger.error("No Gemini SDK installed. Install google-genai to enable live Gemini responses.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}. Falling back to MOCK mode.")
else:
    logger.warning("GEMINI_API_KEY is not set. The LLM service will run in MOCK mode.")

T = TypeVar("T", bound=BaseModel)


def _sanitize_json_schema(schema: Any) -> Any:
    """Recursively remove keys unsupported by Google GenAI Schema specification."""
    if isinstance(schema, dict):
        clean = {}
        for k, v in schema.items():
            if k in {"default", "title", "additionalProperties", "$schema", "$defs"}:
                continue
            clean[k] = _sanitize_json_schema(v)
        return clean
    elif isinstance(schema, list):
        return [_sanitize_json_schema(item) for item in schema]
    return schema


class GeminiClient:
    MODEL_TEXT = settings.GEMINI_MODEL_TEXT
    MODEL_EMBED = settings.GEMINI_MODEL_EMBED

    @classmethod
    def _sdk_model_name(cls, model_name: str) -> str:
        return model_name.removeprefix("models/")

    @classmethod
    def _text_model_names(cls) -> List[str]:
        fallback_models = [
            model.strip()
            for model in settings.GEMINI_MODEL_TEXT_FALLBACKS.split(",")
            if model.strip()
        ]
        return list(dict.fromkeys([cls.MODEL_TEXT, *fallback_models]))

    @classmethod
    async def generate_structured_output(
        cls, prompt: str, schema: Type[T], system_instruction: Optional[str] = None
    ) -> T:
        """Call Gemini to get a structured JSON output conforming to a Pydantic schema."""
        if not is_gemini_active:
            return cls._mock_structured_output(prompt, schema)

        raw_schema = schema.model_json_schema()
        clean_schema = _sanitize_json_schema(raw_schema)

        for model_name in cls._text_model_names():
            try:
                if _genai_client:
                    response = await _genai_client.aio.models.generate_content(
                        model=cls._sdk_model_name(model_name),
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=clean_schema,
                            temperature=0.1,
                        ),
                    )
                    if getattr(response, "parsed", None) is not None:
                        parsed = response.parsed
                        return parsed if isinstance(parsed, schema) else schema.model_validate(parsed)

                    data = json.loads(response.text)
                    return schema.model_validate(data)

                model = legacy_genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                response = model.generate_content(
                    prompt,
                    generation_config=legacy_genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=0.1
                    )
                )
                data = json.loads(response.text)
                return schema.model_validate(data)
            except Exception as e:
                logger.warning(f"Gemini structured generation failed with {model_name}: {e}")

        logger.error("All Gemini structured generation models failed. Using mock fallback.")
        return cls._mock_structured_output(prompt, schema)

    @classmethod
    async def generate_text(cls, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate plain text from Gemini."""
        if not is_gemini_active:
            return (
                f"[MOCK REPLY] AI is running in mock mode. "
                f"Add a valid GEMINI_API_KEY to .env to enable live responses. "
                f"Query: '{prompt[:80]}...'"
            )
        last_error: Optional[Exception] = None
        for model_name in cls._text_model_names():
            try:
                if _genai_client:
                    response = await _genai_client.aio.models.generate_content(
                        model=cls._sdk_model_name(model_name),
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=system_instruction,
                        ) if system_instruction else None,
                    )
                    return response.text or ""

                model = legacy_genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini text generation failed with {model_name}: {e}")

        logger.error(f"All Gemini text generation models failed: {last_error}")
        return f"[ERROR] Gemini call failed: {last_error}"

    @classmethod
    async def get_embedding(cls, text: str) -> List[float]:
        """Generate 768-dimensional text embeddings using Gemini embeddings."""
        if not is_gemini_active:
            return cls._mock_embedding(text)
        try:
            if _genai_client:
                embed_model = cls._sdk_model_name(cls.MODEL_EMBED)
                config_kwargs = {"output_dimensionality": 768}
                if embed_model == "gemini-embedding-001":
                    config_kwargs["task_type"] = "RETRIEVAL_DOCUMENT"

                result = await _genai_client.aio.models.embed_content(
                    model=embed_model,
                    contents=text,
                    config=genai_types.EmbedContentConfig(**config_kwargs),
                )
                return list(result.embeddings[0].values)

            result = legacy_genai.embed_content(
                model=cls.MODEL_EMBED,
                content=text,
                task_type="retrieval_document",
                output_dimensionality=768
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Gemini embedding generation failed: {e}. Using mock fallback.")
            return cls._mock_embedding(text)

    @staticmethod
    def _mock_embedding(text: str) -> List[float]:
        """Deterministic normalized 768-dim mock embedding based on text hash."""
        seed = sum(ord(c) for c in text)
        random.seed(seed)
        emb = [random.uniform(-1, 1) for _ in range(768)]
        norm = sum(x * x for x in emb) ** 0.5
        return [x / norm for x in emb]

    @classmethod
    def _extract_mock_task_details(cls, prompt: str) -> tuple[str, str, Optional[str], str]:
        """Extract a meaningful title, description, priority, and due date from the user prompt."""
        cleaned = prompt.strip()
        # Remove wrapper if passed
        if "'" in cleaned:
            parts = cleaned.split("'")
            if len(parts) >= 3 and len(parts[1]) > 5:
                cleaned = parts[1].strip()

        raw_prompt = cleaned
        # Strip common action prefixes
        for prefix in [
            "schedule a meeting with", "schedule a meeting", "schedule meeting with", "schedule meeting",
            "schedule a task to", "schedule a task for", "schedule a task:", "schedule task:", "schedule task",
            "schedule a", "schedule an", "schedule",
            "remind me to", "remind me",
            "create a high priority task:", "create a high priority task to", "create a priority task:",
            "create a task to", "create a task:", "create a task", "create task:", "create task",
            "add a task to", "add a task:", "add a task", "add task:", "add task",
            "todo:", "todo"
        ]:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip(" :,-")
                break

        title = cleaned.capitalize() if cleaned else "New Task"
        if len(title) > 60:
            title = title[:60].rsplit(" ", 1)[0]

        description = raw_prompt

        priority = "high" if "high" in raw_prompt.lower() or "urgent" in raw_prompt.lower() else "normal"

        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        due_date = None
        if "tomorrow" in raw_prompt.lower():
            due_date = (now + timedelta(days=1)).replace(hour=17, minute=0, second=0).isoformat()
        elif "tonight" in raw_prompt.lower():
            due_date = now.replace(hour=20, minute=0, second=0).isoformat()
        elif "today" in raw_prompt.lower():
            due_date = now.replace(hour=18, minute=0, second=0).isoformat()

        return title, description, due_date, priority

    @classmethod
    def _mock_structured_output(cls, prompt: str, schema: Type[T]) -> T:
        """Heuristic mock outputs for local development without API keys."""
        logger.info(f"Generating mock structured output for schema: {schema.__name__}")
        user_text = prompt
        if "'" in prompt:
            parts = prompt.split("'")
            if len(parts) >= 3:
                user_text = parts[1]
        prompt_lower = user_text.lower()

        if schema.__name__ == "IntentRouterOutput":
            intent = "GENERAL_CHAT"
            title = None
            description = None
            due_date = None
            priority = "normal"
            task_search_query = None
            sql_search_filter = None

            if any(kw in prompt_lower for kw in ["remind", "todo", "task", "call", "meeting", "schedule"]):
                if any(kw in prompt_lower for kw in ["delete", "remove", "cancel"]):
                    intent = "DELETE_TASK"
                    task_search_query = prompt.strip()
                elif any(kw in prompt_lower for kw in ["update", "edit", "change", "reschedule"]):
                    intent = "UPDATE_TASK"
                    task_search_query = prompt.strip()
                    title, description, due_date, priority = cls._extract_mock_task_details(user_text)
                elif any(kw in prompt_lower for kw in ["complete", "done", "finish", "completed"]):
                    intent = "COMPLETE_TASK"
                    task_search_query = prompt.strip()
                else:
                    intent = "CREATE_TASK"
                    title, description, due_date, priority = cls._extract_mock_task_details(user_text)
            elif any(kw in prompt_lower for kw in ["list", "show", "find", "what do i", "search"]):
                if any(kw in prompt_lower for kw in ["today", "tomorrow", "calendar", "week", "schedule"]):
                    intent = "CALENDAR_QUERY"
                else:
                    intent = "QUERY_DATABASE"
                sql_search_filter = prompt.strip()
            elif any(kw in prompt_lower for kw in ["productivity", "analytics", "stats", "how many", "completion"]):
                intent = "ANALYTICS"
            elif any(kw in prompt_lower for kw in ["remember", "memory", "forgot", "recall"]):
                intent = "AI_MEMORY"

            return schema(
                intent=intent,
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                task_search_query=task_search_query,
                sql_search_filter=sql_search_filter,
                chat_reply_suggestion=f"[Mock Route: {intent}] {title or 'Request processed'}"
            )

        if schema.__name__ == "MultiAgentPlan":
            from schemas.ai import SubTask, MultiAgentPlan
            sub_tasks = []
            
            # Check for multiple intents or keywords
            if any(kw in prompt_lower for kw in ["remind", "todo", "task", "call", "meeting", "schedule"]):
                title, description, due_date, priority = cls._extract_mock_task_details(user_text)
                sub_tasks.append(SubTask(
                    task_id=f"task_{len(sub_tasks)+1}",
                    intent="CREATE_TASK",
                    agent_target="task_worker",
                    title=title,
                    description=description,
                    priority=priority,
                    due_date=due_date,
                    sub_prompt=prompt
                ))

            if any(kw in prompt_lower for kw in ["productivity", "analytics", "stats", "how many", "completion"]):
                sub_tasks.append(SubTask(
                    task_id=f"task_{len(sub_tasks)+1}",
                    intent="ANALYTICS",
                    agent_target="analytics_worker",
                    analytics_metric="completion_rate",
                    sub_prompt=prompt
                ))

            if any(kw in prompt_lower for kw in ["calendar", "agenda", "today's schedule", "today's tasks", "scheduled today", "my schedule"]):
                sub_tasks.append(SubTask(
                    task_id=f"task_{len(sub_tasks)+1}",
                    intent="CALENDAR_QUERY",
                    agent_target="task_worker",
                    sub_prompt=prompt
                ))

            if any(kw in prompt_lower for kw in ["remember", "memory", "forgot", "recall"]):
                sub_tasks.append(SubTask(
                    task_id=f"task_{len(sub_tasks)+1}",
                    intent="AI_MEMORY",
                    agent_target="memory_worker",
                    sub_prompt=prompt
                ))

            if not sub_tasks:
                sub_tasks.append(SubTask(
                    task_id="task_1",
                    intent="GENERAL_CHAT",
                    agent_target="chat_worker",
                    sub_prompt=prompt
                ))

            return schema(
                is_multi_intent=len(sub_tasks) > 1,
                user_query=prompt,
                sub_tasks=sub_tasks
            )

        if schema.__name__ == "MemoryExtraction":
            return schema(
                summary="NONE",
                importance_score=1.0
            )

        # Generic fallback
        fields: dict = {}
        for name, field in schema.model_fields.items():
            ann = field.annotation
            if ann in (str, Optional[str]):
                fields[name] = f"[MOCK] {name}"
            elif ann == float:
                fields[name] = 1.0
            elif ann == int:
                fields[name] = 0
            else:
                fields[name] = None
        return schema(**fields)

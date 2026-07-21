import logging
import json
import random
from typing import List, Optional, Type, TypeVar

try:
    import google.generativeai as genai
    _USE_LEGACY_SDK = True
except Exception:
    _USE_LEGACY_SDK = False

from pydantic import BaseModel
from core.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini API if key is available
is_gemini_active = False
if settings.GEMINI_API_KEY:
    try:
        if _USE_LEGACY_SDK:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        is_gemini_active = True
        logger.info("Gemini API initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}. Falling back to MOCK mode.")
else:
    logger.warning("GEMINI_API_KEY is not set. The LLM service will run in MOCK mode.")

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    MODEL_TEXT = settings.GEMINI_MODEL_TEXT
    MODEL_EMBED = settings.GEMINI_MODEL_EMBED

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

        for model_name in cls._text_model_names():
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
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
                model = genai.GenerativeModel(
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
            result = genai.embed_content(
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
    def _mock_structured_output(cls, prompt: str, schema: Type[T]) -> T:
        """Heuristic mock outputs for local development without API keys."""
        logger.info(f"Generating mock structured output for schema: {schema.__name__}")
        prompt_lower = prompt.lower()

        if schema.__name__ == "IntentRouterOutput":
            intent = "GENERAL_CHAT"
            title = None
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
                    title = "Updated Task"
                elif any(kw in prompt_lower for kw in ["complete", "done", "finish", "completed"]):
                    intent = "COMPLETE_TASK"
                    task_search_query = prompt.strip()
                else:
                    intent = "CREATE_TASK"
                    title = "New Scheduled Task"
                    due_date = "2026-07-05T20:00:00" if "tomorrow" in prompt_lower else None
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
                due_date=due_date,
                priority=priority,
                task_search_query=task_search_query,
                sql_search_filter=sql_search_filter,
                chat_reply_suggestion=f"[Mock Route: {intent}] Set GEMINI_API_KEY for live AI."
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

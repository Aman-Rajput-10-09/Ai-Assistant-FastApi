from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Scheduling Assistant Backend"
    ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:////tmp/dev.db"

    # Security
    SECRET_KEY: str = "production-grade-development-jwt-signing-key-secret-392810"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_TEXT: str = "gemini-3.5-flash"
    GEMINI_MODEL_TEXT_FALLBACKS: str = "gemini-flash-latest,gemini-2.5-flash"
    GEMINI_MODEL_EMBED: str = "models/gemini-embedding-001"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "NexusAI - Intelligent Inference Gateway"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Security & Auth
    API_KEYS: str = "sk-nexus-dev-demo-key,sk-test-client-123"

    # Redis & Storage
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_IN_MEMORY_FALLBACK: bool = True

    # Semantic Caching
    SIMILARITY_THRESHOLD: float = 0.92
    DEFAULT_CACHE_TTL_SECONDS: int = 3600  # 1 hour

    # Rate Limiting
    RATE_LIMIT_MAX_REQUESTS: int = 30
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # LLM Providers: "mock", "huggingface", "openai"
    DEFAULT_LLM_PROVIDER: str = "mock"

    # Hugging Face Configuration
    HF_API_TOKEN: str | None = None
    HF_MODEL_NAME: str = "google/flan-t5-base"

    # OpenAI / OpenRouter Compatible Configuration
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"

    @property
    def valid_api_keys(self) -> list[str]:
        return [k.strip() for k in self.API_KEYS.split(",") if k.strip()]


settings = Settings()

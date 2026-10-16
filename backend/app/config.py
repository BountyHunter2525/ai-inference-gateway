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

    # Advanced Cache Management (Option 3)
    CACHE_MAX_ENTRIES: int = 500          # LRU eviction kicks in above this limit
    CACHE_WARMING_ENABLED: bool = True    # Run seed-query warmer on startup
    # Pipe-separated seed prompts for cache warming. Set to "" to disable.
    CACHE_WARM_QUERIES: str = (
        "What is the capital of France?|"
        "Explain how TCP/IP works|"
        "What is machine learning?|"
        "How does the internet work?|"
        "What is a neural network?|"
        "Explain the OSI model|"
        "What is REST API?|"
        "How does HTTPS work?|"
        "What is Docker?|"
        "Explain microservices architecture"
    )

    # Adaptive TTL windows (seconds) per query category
    CACHE_TTL_FACTUAL: int = 86400        # 24 h  — stable facts, definitions
    CACHE_TTL_TECHNICAL: int = 21600      # 6 h   — code, how-to, architecture
    CACHE_TTL_GENERAL: int = 3600         # 1 h   — everything else

    @property
    def warm_queries_list(self) -> list[str]:
        return [q.strip() for q in self.CACHE_WARM_QUERIES.split("|") if q.strip()]

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

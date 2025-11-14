"""Configuration settings for the gateway service."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "duckdb:///./gateway.db"
    SQLITE_URL: str = "sqlite:///./usage_logs.db"
    POSTGRES_URL: str = "postgresql://llm_user:llm_password@localhost:5432/llm_templates"
    
    # LiteLLM Configuration
    LITELLM_VERBOSE: bool = False
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_ENABLED: bool = True
    
    # API Keys (for LLM providers)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Ollama Configuration
    OLLAMA_API_BASE: str = "http://localhost:11434"
    OLLAMA_CHECK_MODELS: str = ""  # Comma-separated list of required models
    OLLAMA_ENABLED: bool = True  # Auto-detect or explicitly enable/disable

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

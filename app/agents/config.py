
"""Centralized configuration for the TalentFlow AI agent."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Validated application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # OpenAI configuration
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    openai_timeout: float = Field(default=60.0, gt=0)
    openai_max_retries: int = Field(default=2, ge=0, le=10)

    # LangSmith configuration
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "talentflow-ai"
    langsmith_tracing: bool = False

    # Resume validation limits
    max_resume_size_mb: int = Field(default=5, ge=1, le=20)
    max_resume_pages: int = Field(default=30, ge=1, le=100)
    max_resume_characters: int = Field(default=100_000, ge=1_000)


@lru_cache(maxsize=1)
def get_settings() -> AgentSettings:
    """Return cached application settings."""
    return AgentSettings()

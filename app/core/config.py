
import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------
# 1. Environment configuration
# --------------------------------------------------

# Development:
#   Load .env and override stale terminal variables.
#
# Production:
#   Preserve environment variables supplied by
#   the deployment platform.
#
# Set APP_ENV=production on the deployment platform.

APP_ENV = os.getenv(
    "APP_ENV",
    "development",
).strip().lower()

load_dotenv(
    override=(APP_ENV == "development")
)


# --------------------------------------------------
# 2. Application settings
# --------------------------------------------------

class Settings(BaseModel):
    openai_api_key: str = Field(min_length=1)

    openai_model: str = Field(
        default="gpt-5.6-luna",
        min_length=1,
    )

    openai_timeout: float = Field(
        default=60.0,
        gt=0,
    )

    openai_max_retries: int = Field(
        default=2,
        ge=0,
    )

    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        value = value.strip()

        placeholders = {
            "your-api-key",
            "your_existing_key",
            "sk-your-actual-openai-key",
        }

        if not value:
            raise ValueError(
                "OPENAI_API_KEY cannot be empty."
            )

        if value.lower() in placeholders:
            raise ValueError(
                "OPENAI_API_KEY contains a placeholder."
            )

        return value

    @field_validator("openai_model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "OPENAI_MODEL cannot be empty."
            )

        return value


# --------------------------------------------------
# 3. Cached settings
# --------------------------------------------------

@lru_cache
def get_settings() -> Settings:
    api_key = os.getenv(
        "OPENAI_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. "
            "Configure it in your environment."
        )

    return Settings(
        openai_api_key=api_key,
        openai_model=os.getenv(
            "OPENAI_MODEL",
            "gpt-5.6-luna",
        ),
        openai_timeout=os.getenv(
            "OPENAI_TIMEOUT",
            "60",
        ),
        openai_max_retries=os.getenv(
            "OPENAI_MAX_RETRIES",
            "2",
        ),
    )

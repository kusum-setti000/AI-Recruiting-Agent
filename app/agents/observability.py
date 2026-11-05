
"""LangSmith tracing configuration for TalentFlow AI."""

import logging
from contextlib import contextmanager

from langsmith import tracing_context

from app.agents.config import get_settings


logger = logging.getLogger(__name__)


@contextmanager
def get_tracing_context():
    """Control LangSmith tracing for candidate screening."""

    settings = get_settings()

    if settings.langsmith_tracing:
        raise RuntimeError(
            "Candidate tracing is disabled until PII redaction is implemented."
        )

    with tracing_context(enabled=False):
        yield

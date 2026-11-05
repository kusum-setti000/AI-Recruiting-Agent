
"""LangChain models and structured-output chains for TalentFlow AI."""

import json

from langchain_openai import ChatOpenAI

from app.agents.config import get_settings
from app.agents.prompts import (
    JOB_ALIGNMENT_PROMPT,
    CANDIDATE_SCREENING_PROMPT,
)
from app.agents.schemas import (
    CandidateAnalysis,
    JobAlignment,
)
from app.agents.scoring import assessment_from_score


def create_chat_model() -> ChatOpenAI:
    """Create the configured LangChain OpenAI chat model."""

    settings = get_settings()

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
        timeout=settings.openai_timeout,
        max_retries=settings.openai_max_retries,
    )


def create_alignment_chain():
    """Create the job-description alignment chain."""

    model = create_chat_model()

    structured_model = model.with_structured_output(
        JobAlignment,
        method="json_schema",
    )

    return JOB_ALIGNMENT_PROMPT | structured_model


def create_screening_chain():
    """Create the candidate-screening chain."""

    model = create_chat_model()

    structured_model = model.with_structured_output(
        CandidateAnalysis,
        method="json_schema",
    )

    return CANDIDATE_SCREENING_PROMPT | structured_model


def validate_job_alignment(
    job_title: str,
    job_description: str,
) -> JobAlignment:
    """Check whether the job title and description are consistent."""

    chain = create_alignment_chain()

    job_data = json.dumps(
        {
            "job_title": job_title,
            "job_description": job_description,
        },
        ensure_ascii=False,
    )

    result = chain.invoke({"job_data": job_data})

    if not isinstance(result, JobAlignment):
        raise ValueError("Invalid job alignment response.")

    return result


def analyze_candidate(
    job_title: str,
    job_description: str,
    resume_text: str,
) -> CandidateAnalysis:
    """Analyze a candidate using structured LangChain output."""

    chain = create_screening_chain()

    result = chain.invoke(
        {
            "job_title": job_title,
            "job_description": job_description,
            "resume_text": resume_text,
        }
    )

    if not isinstance(result, CandidateAnalysis):
        raise ValueError("Invalid candidate analysis response.")

    # Enforce the deterministic score-band mapping.
    result.overall_assessment = assessment_from_score(
        result.match_score
    )

    return result

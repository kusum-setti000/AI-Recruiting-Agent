
"""LangGraph processing nodes for TalentFlow AI."""

from typing import Any, TypedDict

from app.agents.document_loader import (
    load_resume,
    validate_resume_upload,
)
from app.agents.models import (
    analyze_candidate,
    validate_job_alignment,
)
from app.agents.scoring import assessment_from_score


class ScreeningState(TypedDict, total=False):
    """Shared state passed between LangGraph nodes."""

    job_title: str
    job_description: str

    resume_filename: str
    resume_bytes: bytes
    resume_text: str

    job_alignment: dict[str, Any]
    ai_analysis: dict[str, Any]


def validate_alignment_node(
    state: ScreeningState,
) -> dict[str, Any]:
    """Check job alignment before expensive resume extraction."""

    job_title = state["job_title"].strip()
    job_description = state["job_description"].strip()

    if not job_title or not job_description:
        raise ValueError(
            "Job title and description are required."
        )

    # Validate the upload without extracting its contents.
    validate_resume_upload(
        filename=state["resume_filename"],
        file_bytes=state["resume_bytes"],
    )

    alignment = validate_job_alignment(
        job_title=job_title,
        job_description=job_description,
    )

    return {
        "job_title": job_title,
        "job_description": job_description,
        "job_alignment": alignment.model_dump(),
    }


def route_after_alignment(state: ScreeningState) -> str:
    """Select the next step based on job alignment."""

    alignment = state.get("job_alignment") or {}

    if alignment.get("status") == "aligned":
        return "load_resume"

    return "stop"


def load_resume_node(
    state: ScreeningState,
) -> dict[str, str]:
    """Extract resume text with LangChain document loaders."""

    resume_text = load_resume(
        filename=state["resume_filename"],
        file_bytes=state["resume_bytes"],
    )

    return {"resume_text": resume_text}


def analyze_candidate_node(
    state: ScreeningState,
) -> dict[str, Any]:
    """Generate structured candidate analysis with LangChain."""

    analysis = analyze_candidate(
        job_title=state["job_title"],
        job_description=state["job_description"],
        resume_text=state["resume_text"],
    )

    return {"ai_analysis": analysis.model_dump()}


def validate_output_node(
    state: ScreeningState,
) -> dict[str, Any]:
    """Ensure the assessment matches the score band."""

    analysis = state.get("ai_analysis")

    if not isinstance(analysis, dict):
        raise ValueError(
            "Candidate analysis is missing or invalid."
        )

    score = analysis.get("match_score")

    expected_assessment = assessment_from_score(score)

    if analysis.get("overall_assessment") != expected_assessment:
        raise ValueError(
            "Candidate assessment does not match its score."
        )

    return {"ai_analysis": analysis}

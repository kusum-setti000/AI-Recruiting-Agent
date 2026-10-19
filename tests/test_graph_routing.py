
"""Integration tests for TalentFlow LangGraph routing."""

from unittest.mock import patch

import pymupdf

from app.agents.graph import create_screening_graph
from app.agents.schemas import CandidateAnalysis, JobAlignment


def make_resume() -> bytes:
    """Generate a valid PDF without external test files."""
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "Python developer with ML experience")
        return pdf.tobytes()


def test_conflicting_job_description_stops_workflow():
    """Conflict must stop before resume extraction and AI screening."""

    alignment = JobAlignment(
        status="conflict",
        reason="Job title and description describe different roles.",
    )

    with (
        patch(
            "app.agents.nodes.validate_job_alignment",
            return_value=alignment,
        ),
        patch("app.agents.nodes.load_resume") as mock_loader,
        patch("app.agents.nodes.analyze_candidate") as mock_analysis,
    ):
        result = create_screening_graph().invoke(
            {
                "job_title": "Data Scientist",
                "job_description": "Hiring an accountant.",
                "resume_filename": "resume.pdf",
                "resume_bytes": make_resume(),
            }
        )

    assert result["job_alignment"]["status"] == "conflict"
    assert result.get("ai_analysis") is None
    mock_loader.assert_not_called()
    mock_analysis.assert_not_called()


def test_aligned_job_completes_screening():
    """Aligned job must execute extraction, analysis, and validation."""

    alignment = JobAlignment(
        status="aligned",
        reason="Job title matches the required responsibilities.",
    )

    analysis = CandidateAnalysis(
        match_score=90,
        matching_skills=["Python", "Machine Learning"],
        missing_skills=["Docker"],
        candidate_strengths=["ML engineering experience"],
        experience_alignment="Relevant machine learning experience.",
        potential_gaps=["Limited Docker experience"],
        recruiter_questions=["Describe your ML deployment experience."],
        overall_assessment="Strong Match",
        assessment_reasoning="Candidate meets most job requirements.",
    )

    with (
        patch(
            "app.agents.nodes.validate_job_alignment",
            return_value=alignment,
        ),
        patch(
            "app.agents.nodes.load_resume",
            return_value="Python developer with ML experience",
        ) as mock_loader,
        patch(
            "app.agents.nodes.analyze_candidate",
            return_value=analysis,
        ) as mock_analysis,
    ):
        result = create_screening_graph().invoke(
            {
                "job_title": "Machine Learning Engineer",
                "job_description": "Python and machine learning experience.",
                "resume_filename": "resume.pdf",
                "resume_bytes": make_resume(),
            }
        )

    assert result["job_alignment"]["status"] == "aligned"
    assert result["ai_analysis"]["match_score"] == 90
    assert result["ai_analysis"]["overall_assessment"] == "Strong Match"

    mock_loader.assert_called_once()
    mock_analysis.assert_called_once_with(
        job_title="Machine Learning Engineer",
        job_description="Python and machine learning experience.",
        resume_text="Python developer with ML experience",
    )

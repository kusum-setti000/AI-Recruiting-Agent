
"""Tests for the Streamlit-facing screening entry point."""

from unittest.mock import patch

import pytest

from app.agents.graph import run_screening_graph


@pytest.mark.parametrize(
    "status,analysis",
    [
        ("aligned", {"match_score": 90, "overall_assessment": "Strong Match"}),
        ("conflict", None),
    ],
)
def test_screening_response_contract(status, analysis):
    """Return the response structure expected by Streamlit."""

    final_state = {
        "job_alignment": {
            "status": status,
            "reason": "Test alignment result.",
        },
        "ai_analysis": analysis,
    }

    with patch("app.agents.graph.create_screening_graph") as mock_graph:
        mock_graph.return_value.invoke.return_value = final_state

        result = run_screening_graph(
            job_title="  Data Scientist  ",
            job_description="Python and machine learning",
            resume_filename="resume.pdf",
            resume_bytes=b"test",
        )

    assert result == {
        "candidate_resume": "resume.pdf",
        "job_title": "Data Scientist",
        "job_alignment": final_state["job_alignment"],
        "ai_analysis": analysis,
    }

    mock_graph.return_value.invoke.assert_called_once()


def test_invalid_resume_bytes():
    """Reject invalid resume data before graph execution."""

    with pytest.raises(TypeError, match="resume_bytes must be bytes"):
        run_screening_graph(
            job_title="Data Scientist",
            job_description="Python experience",
            resume_filename="resume.pdf",
            resume_bytes="not bytes",
        )

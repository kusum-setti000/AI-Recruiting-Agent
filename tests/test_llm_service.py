
import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.models.schemas import CandidateAnalysis, JobAlignment
from app.services.llm_service import (
    analyze_with_llm,
    validate_job_alignment,
)


JOB_TITLE = "Python Developer"
JOB_DESCRIPTION = (
    "Develop Python APIs using FastAPI, "
    "SQL, and automated testing."
)


def make_analysis(
    score=85,
    assessment="Strong Match",
):
    return CandidateAnalysis(
        match_score=score,
        matching_skills=["Python", "FastAPI"],
        missing_skills=["Docker"],
        candidate_strengths=["API development"],
        experience_alignment="Relevant experience",
        potential_gaps=["Limited Docker evidence"],
        recruiter_questions=[
            "Have you deployed applications using Docker?"
        ],
        overall_assessment=assessment,
        assessment_reasoning=(
            "The candidate demonstrates relevant skills."
        ),
    )


# --------------------------------------------------
# Job alignment tests
# --------------------------------------------------

@pytest.mark.parametrize(
    "status",
    ["aligned", "conflict", "unclear"],
)
def test_job_alignment_returns_structured_result(status):
    expected = JobAlignment(
        status=status,
        reason=f"Synthetic {status} result.",
    )

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = expected

    with patch(
        "app.services.llm_service.alignment_chain",
        mock_chain,
    ):
        result = validate_job_alignment(
            JOB_TITLE,
            JOB_DESCRIPTION,
        )

    assert isinstance(result, JobAlignment)
    assert result.status == status
    assert result.reason == expected.reason

    mock_chain.invoke.assert_called_once()


def test_job_alignment_passes_correct_input():
    expected = JobAlignment(
        status="aligned",
        reason="The role is consistent.",
    )

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = expected

    with patch(
        "app.services.llm_service.alignment_chain",
        mock_chain,
    ):
        validate_job_alignment(
            JOB_TITLE,
            JOB_DESCRIPTION,
        )

    payload = mock_chain.invoke.call_args.args[0]
    job_data = json.loads(payload["job_data"])

    assert job_data == {
        "job_title": JOB_TITLE,
        "job_description": JOB_DESCRIPTION,
    }


def test_job_alignment_handles_missing_response():
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = None

    with patch(
        "app.services.llm_service.alignment_chain",
        mock_chain,
    ):
        with pytest.raises(
            RuntimeError,
            match="job alignment result",
        ):
            validate_job_alignment(
                JOB_TITLE,
                JOB_DESCRIPTION,
            )


def test_job_alignment_propagates_service_error():
    mock_chain = MagicMock()
    mock_chain.invoke.side_effect = RuntimeError(
        "Synthetic alignment service failure"
    )

    with patch(
        "app.services.llm_service.alignment_chain",
        mock_chain,
    ):
        with pytest.raises(
            RuntimeError,
            match="Synthetic alignment service failure",
        ):
            validate_job_alignment(
                JOB_TITLE,
                JOB_DESCRIPTION,
            )


# --------------------------------------------------
# Candidate screening tests
# --------------------------------------------------

@pytest.mark.parametrize(
    "score, expected_assessment",
    [
        (0, "Weak Match"),
        (49, "Weak Match"),
        (50, "Needs Human Review"),
        (69, "Needs Human Review"),
        (70, "Potential Match"),
        (84, "Potential Match"),
        (85, "Strong Match"),
        (100, "Strong Match"),
    ],
)
def test_screening_assigns_correct_assessment(
    score,
    expected_assessment,
):
    analysis = make_analysis(
        score=score,
        assessment="Strong Match",
    )

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = analysis

    with patch(
        "app.services.llm_service.screening_chain",
        mock_chain,
    ):
        result = analyze_with_llm(
            "Synthetic screening prompt"
        )

    assert isinstance(result, CandidateAnalysis)
    assert result.match_score == score
    assert (
        result.overall_assessment
        == expected_assessment
    )


def test_screening_passes_correct_prompt():
    prompt = "Evaluate synthetic candidate evidence."

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = make_analysis()

    with patch(
        "app.services.llm_service.screening_chain",
        mock_chain,
    ):
        analyze_with_llm(prompt)

    mock_chain.invoke.assert_called_once_with(
        {"screening_input": prompt}
    )


def test_screening_handles_missing_response():
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = None

    with patch(
        "app.services.llm_service.screening_chain",
        mock_chain,
    ):
        with pytest.raises(
            RuntimeError,
            match="candidate analysis",
        ):
            analyze_with_llm(
                "Synthetic screening prompt"
            )


def test_screening_propagates_service_error():
    mock_chain = MagicMock()
    mock_chain.invoke.side_effect = RuntimeError(
        "Synthetic screening service failure"
    )

    with patch(
        "app.services.llm_service.screening_chain",
        mock_chain,
    ):
        with pytest.raises(
            RuntimeError,
            match="Synthetic screening service failure",
        ):
            analyze_with_llm(
                "Synthetic screening prompt"
            )


# --------------------------------------------------
# Pydantic schema tests
# --------------------------------------------------

@pytest.mark.parametrize(
    "invalid_score",
    [-1, 101, 150],
)
def test_candidate_schema_rejects_invalid_score(
    invalid_score,
):
    payload = make_analysis().model_dump()
    payload["match_score"] = invalid_score

    with pytest.raises(ValidationError):
        CandidateAnalysis.model_validate(payload)


def test_candidate_schema_rejects_invalid_assessment():
    payload = make_analysis().model_dump()
    payload["overall_assessment"] = "Excellent Candidate"

    with pytest.raises(ValidationError):
        CandidateAnalysis.model_validate(payload)


def test_alignment_schema_rejects_invalid_status():
    with pytest.raises(ValidationError):
        JobAlignment(
            status="approved",
            reason="Invalid status",
        )

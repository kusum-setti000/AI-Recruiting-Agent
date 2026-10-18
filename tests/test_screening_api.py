
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import JobAlignment


client = TestClient(app)

ENDPOINT = "/analyze-candidate"

VALID_JOB_TITLE = "Python Developer"
VALID_JOB_DESCRIPTION = (
    "Develop Python APIs using FastAPI, "
    "SQL databases, and automated testing."
)

VALID_PDF = b"%PDF-1.7\nSynthetic test content"


def make_request(
    filename="resume.pdf",
    content=VALID_PDF,
    job_title=VALID_JOB_TITLE,
    job_description=VALID_JOB_DESCRIPTION,
):
    return client.post(
        ENDPOINT,
        files={
            "file": (
                filename,
                content,
                "application/pdf",
            )
        },
        data={
            "job_title": job_title,
            "job_description": job_description,
        },
    )


def aligned_result():
    return JobAlignment(
        status="aligned",
        reason="The responsibilities match the job title.",
    )


def mock_graph_result():
    return {
        "job_alignment": {
            "status": "aligned",
            "reason": "The responsibilities match the job title.",
        },
        "ai_analysis": {
            "match_score": 85,
            "overall_assessment": "Strong Match",
            "matching_skills": ["Python", "FastAPI"],
            "missing_skills": [],
            "candidate_strengths": ["API development"],
            "experience_alignment": "Relevant experience",
            "potential_gaps": [],
            "recruiter_questions": [],
            "assessment_reasoning": (
                "The resume demonstrates relevant skills."
            ),
        },
    }


def test_successful_candidate_screening():
    with (
        patch(
            "app.api.routes.screening.validate_job_alignment",
            return_value=aligned_result(),
        ) as alignment_mock,
        patch(
            "app.api.routes.screening.read_resume",
            return_value="Python developer with FastAPI experience",
        ) as resume_mock,
        patch(
            "app.api.routes.screening.run_screening_graph",
            return_value=mock_graph_result(),
        ) as graph_mock,
    ):
        response = make_request()

    assert response.status_code == 200

    body = response.json()

    assert body["candidate_resume"] == "resume.pdf"
    assert body["job_title"] == VALID_JOB_TITLE
    assert body["job_alignment"]["status"] == "aligned"
    assert body["ai_analysis"]["match_score"] == 85
    assert body["ai_analysis"]["overall_assessment"] == "Strong Match"

    alignment_mock.assert_called_once()
    resume_mock.assert_called_once()

    graph_mock.assert_called_once_with(
        job_title=VALID_JOB_TITLE,
        job_description=VALID_JOB_DESCRIPTION,
        resume_text="Python developer with FastAPI experience",
        prevalidated_alignment=aligned_result().model_dump(),
    )


@pytest.mark.parametrize(
    "filename",
    ["resume.txt", "resume.exe", "resume.doc"],
)
def test_reject_unsupported_file_types(filename):
    response = make_request(
        filename=filename,
        content=b"Invalid test file",
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "job_title, job_description",
    [
        ("", VALID_JOB_DESCRIPTION),
        (VALID_JOB_TITLE, ""),
        ("   ", VALID_JOB_DESCRIPTION),
        (VALID_JOB_TITLE, "   "),
    ],
)
def test_reject_empty_job_fields(
    job_title,
    job_description,
):
    response = make_request(
        job_title=job_title,
        job_description=job_description,
    )

    assert response.status_code == 422


def test_reject_job_alignment_conflict():
    conflict = JobAlignment(
        status="conflict",
        reason="The job description does not match the title.",
    )

    with (
        patch(
            "app.api.routes.screening.validate_job_alignment",
            return_value=conflict,
        ),
        patch(
            "app.api.routes.screening.read_resume",
        ) as resume_mock,
        patch(
            "app.api.routes.screening.run_screening_graph",
        ) as graph_mock,
    ):
        response = make_request()

    assert response.status_code == 422
    assert response.json()["detail"]["status"] == "conflict"

    resume_mock.assert_not_called()
    graph_mock.assert_not_called()


def test_reject_unclear_job_alignment():
    unclear = JobAlignment(
        status="unclear",
        reason="Insufficient job description details.",
    )

    with patch(
        "app.api.routes.screening.validate_job_alignment",
        return_value=unclear,
    ):
        response = make_request()

    assert response.status_code == 422
    assert response.json()["detail"]["status"] == "unclear"


def test_reject_missing_graph_analysis():
    graph_result = {
        "job_alignment": {
            "status": "aligned",
            "reason": "Valid alignment.",
        },
        "ai_analysis": None,
    }

    with (
        patch(
            "app.api.routes.screening.validate_job_alignment",
            return_value=aligned_result(),
        ),
        patch(
            "app.api.routes.screening.read_resume",
            return_value="Synthetic resume",
        ),
        patch(
            "app.api.routes.screening.run_screening_graph",
            return_value=graph_result,
        ),
    ):
        response = make_request()

    assert response.status_code == 500


def test_handle_unexpected_alignment_error():
    with patch(
        "app.api.routes.screening.validate_job_alignment",
        side_effect=RuntimeError("Synthetic AI service failure"),
    ):
        response = make_request()

    assert response.status_code == 500
    assert "Candidate analysis failed" in response.json()["detail"]


def test_reject_missing_resume():
    response = client.post(
        ENDPOINT,
        data={
            "job_title": VALID_JOB_TITLE,
            "job_description": VALID_JOB_DESCRIPTION,
        },
    )

    assert response.status_code == 422


def test_reject_missing_job_description():
    response = client.post(
        ENDPOINT,
        files={
            "file": (
                "resume.pdf",
                VALID_PDF,
                "application/pdf",
            )
        },
        data={
            "job_title": VALID_JOB_TITLE,
        },
    )

    assert response.status_code == 422

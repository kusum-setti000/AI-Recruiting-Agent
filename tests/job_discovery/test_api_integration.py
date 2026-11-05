"""Integration tests for resume-based job discovery API."""

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
    JobDiscoveryResult,
)
from app.integrations.job_discovery.service import JobDiscoveryService


client = TestClient(app, raise_server_exceptions=False)


def make_profile():
    return CandidateJobProfile(
        target_titles=["Machine Learning Engineer"],
        skills=["Python", "Machine Learning"],
        experience_years=6,
    )


def make_job():
    return DiscoveredJob(
        source="greenhouse",
        external_id="api-test",
        title="Machine Learning Engineer",
        company="Example",
        description="Python and ML. Minimum 5 years of experience.",
        job_url="https://example.com/jobs/api-test",
    )


def fake_discovery(profile):
    class FakeProvider:
        def search(self, candidate_profile):
            return [make_job()]

    return JobDiscoveryService(
        providers=[FakeProvider()]
    ).search(profile)


def upload(client_instance=client, **form_data):
    return client_instance.post(
        "/api/jobs/discover-from-resume",
        files={
            "resume": (
                "resume.pdf",
                b"%PDF-1.4 fake test content",
                "application/pdf",
            )
        },
        data=form_data,
    )


def test_valid_resume_returns_jobs_and_explanations():
    with patch(
        "app.main.profile_from_resume",
        return_value=make_profile(),
    ), patch(
        "app.main.JobDiscoveryService"
    ) as mock_service:
        mock_service.return_value.search.side_effect = fake_discovery

        response = upload()

    assert response.status_code == 200

    body = response.json()

    assert body["total_found"] == 1
    assert body["candidate_profile"]["experience_years"] == 6

    job = body["jobs"][0]

    assert job["match_score"] is not None
    assert job["match_explanation"] is not None
    assert job["recommendation_summary"] is not None
    assert "Python" in job["match_explanation"]["matched_skills"]


def test_location_and_remote_only_forwarded_to_profiler():
    with patch(
        "app.main.profile_from_resume",
        return_value=make_profile(),
    ) as mock_profiler, patch(
        "app.main.JobDiscoveryService"
    ) as mock_service:
        mock_service.return_value.search.return_value = JobDiscoveryResult()

        response = upload(
            location="United States",
            remote_only="true",
        )

    assert response.status_code == 200

    kwargs = mock_profiler.call_args.kwargs

    assert kwargs["location"] == "United States"
    assert kwargs["remote_only"] is True


def test_missing_resume_returns_422():
    response = client.post(
        "/api/jobs/discover-from-resume",
        data={"location": "United States"},
    )

    assert response.status_code == 422


def test_invalid_resume_returns_400():
    from app.agents.document_loader import ResumeValidationError

    with patch(
        "app.main.profile_from_resume",
        side_effect=ResumeValidationError("Invalid resume"),
    ):
        response = upload()

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid resume"


def test_value_error_returns_400():
    with patch(
        "app.main.profile_from_resume",
        side_effect=ValueError("Invalid candidate profile"),
    ):
        response = upload()

    assert response.status_code == 400


def test_empty_discovery_results():
    with patch(
        "app.main.profile_from_resume",
        return_value=make_profile(),
    ), patch(
        "app.main.JobDiscoveryService"
    ) as mock_service:
        mock_service.return_value.search.return_value = JobDiscoveryResult()

        response = upload()

    assert response.status_code == 200
    assert response.json()["total_found"] == 0
    assert response.json()["jobs"] == []


def test_unexpected_error_returns_500():
    with patch(
        "app.main.profile_from_resume",
        side_effect=RuntimeError("Unexpected failure"),
    ):
        response = client.post(
            "/api/jobs/discover-from-resume",
            files={"resume": ("resume.pdf", b"fake", "application/pdf")},
        )

    assert response.status_code == 500

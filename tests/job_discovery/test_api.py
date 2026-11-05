from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
    JobDiscoveryResult,
)

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.main.JobDiscoveryService")
@patch("app.main.profile_from_resume")
def test_resume_discovery_endpoint(mock_profile, mock_service):
    mock_profile.return_value = CandidateJobProfile(
        target_titles=["Software Engineer"],
        skills=["Python", "FastAPI"],
        location="United States",
        remote_only=False,
    )

    job = DiscoveredJob(
        source="greenhouse",
        external_id="12345",
        title="Software Engineer",
        company="Example",
        location="United States",
        job_url="https://example.com/jobs/12345",
    )

    mock_service.return_value.search.return_value = JobDiscoveryResult(
        jobs=[job],
        total_found=1,
        new_jobs=1,
    )

    response = client.post(
        "/api/jobs/discover-from-resume",
        files={
            "resume": (
                "resume.pdf",
                b"synthetic resume bytes",
                "application/pdf",
            )
        },
        data={
            "location": "United States",
            "remote_only": "false",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total_found"] == 1
    assert len(body["jobs"]) == 1
    assert body["jobs"][0]["title"] == "Software Engineer"
    assert body["candidate_profile"]["skills"] == [
        "Python",
        "FastAPI",
    ]

    mock_profile.assert_called_once_with(
        filename="resume.pdf",
        file_bytes=b"synthetic resume bytes",
        location="United States",
        remote_only=False,
    )


@patch("app.main.profile_from_resume")
def test_invalid_resume_returns_400(mock_profile):
    mock_profile.side_effect = ValueError("Invalid resume")

    response = client.post(
        "/api/jobs/discover-from-resume",
        files={
            "resume": (
                "invalid.pdf",
                b"invalid content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid resume"


def test_missing_resume_returns_422():
    response = client.post(
        "/api/jobs/discover-from-resume"
    )

    assert response.status_code == 422

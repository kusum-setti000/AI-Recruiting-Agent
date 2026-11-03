import pytest
from unittest.mock import Mock, patch

from app.integrations.job_discovery.greenhouse import GreenhouseProvider
from app.integrations.job_discovery.models import CandidateJobProfile


@patch("app.integrations.job_discovery.greenhouse.requests.get")
def test_greenhouse_search(mock_get):
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "jobs": [
            {
                "id": 12345,
                "title": "Python Developer",
                "location": {"name": "Houston, TX"},
                "content": "<p>Python and FastAPI development</p>",
                "absolute_url": "https://job-boards.greenhouse.io/example/jobs/12345",
            }
        ]
    }

    mock_get.return_value = response

    profile = CandidateJobProfile(
        target_titles=["Python Developer"],
        skills=["Python"],
        location="Houston",
    )

    jobs = GreenhouseProvider(
        board_tokens=["example"]
    ).search(profile)

    assert len(jobs) == 1
    assert jobs[0].title == "Python Developer"
    assert jobs[0].source == "greenhouse"
    assert jobs[0].location == "Houston, TX"
    assert "FastAPI" in jobs[0].description


def test_greenhouse_rejects_invalid_board_token():
    profile = CandidateJobProfile()

    with pytest.raises(ValueError, match="Invalid Greenhouse board token"):
        GreenhouseProvider(
            board_tokens=["../invalid"]
        ).search(profile)

@patch("app.integrations.job_discovery.greenhouse.requests.get")
def test_us_search_excludes_european_remote_jobs(mock_get):
    response = Mock()
    response.json.return_value = {
        "jobs": [
            {
                "id": 101,
                "title": "AI Engineer",
                "location": {"name": "France, Remote; Spain, Remote"},
                "content": "<p>Python and machine learning</p>",
                "absolute_url": "https://example.com/jobs/101",
            },
            {
                "id": 102,
                "title": "AI Engineer",
                "location": {"name": "United States, Remote"},
                "content": "<p>Python and machine learning</p>",
                "absolute_url": "https://example.com/jobs/102",
            },
        ]
    }
    mock_get.return_value = response

    profile = CandidateJobProfile(
        target_titles=["AI Engineer"],
        skills=["Python"],
        location="United States",
    )

    jobs = GreenhouseProvider(
        board_tokens=["example"]
    ).search(profile)

    assert len(jobs) == 1
    assert jobs[0].external_id == "102"


@patch("app.integrations.job_discovery.greenhouse.requests.get")
def test_us_remote_only_excludes_european_remote_jobs(mock_get):
    response = Mock()
    response.json.return_value = {
        "jobs": [
            {
                "id": 201,
                "title": "ML Engineer",
                "location": {"name": "Germany, Remote"},
                "content": "<p>Python and machine learning</p>",
                "absolute_url": "https://example.com/jobs/201",
            },
            {
                "id": 202,
                "title": "ML Engineer",
                "location": {"name": "United States, Remote"},
                "content": "<p>Python and machine learning</p>",
                "absolute_url": "https://example.com/jobs/202",
            },
        ]
    }
    mock_get.return_value = response

    profile = CandidateJobProfile(
        target_titles=["ML Engineer"],
        location="United States",
        remote_only=True,
    )

    jobs = GreenhouseProvider(
        board_tokens=["example"]
    ).search(profile)

    assert len(jobs) == 1
    assert jobs[0].external_id == "202"

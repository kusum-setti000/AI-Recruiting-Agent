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

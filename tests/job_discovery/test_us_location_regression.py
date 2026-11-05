import pytest
from unittest.mock import Mock, patch

from app.integrations.job_discovery.greenhouse import GreenhouseProvider
from app.integrations.job_discovery.models import CandidateJobProfile


@pytest.mark.parametrize(
    "location,expected",
    [
        ("Houston, TX", True),
        ("New York, NY", True),
        ("Seattle, WA", True),
        ("Remote - United States", True),
        ("Remote - USA", True),
        ("Remote - Germany", False),
        ("London, United Kingdom", False),
        ("Toronto, Canada", False),
    ],
)
@patch("app.integrations.job_discovery.greenhouse.requests.get")
def test_us_location_filtering_regression(mock_get, location, expected):
    response = Mock()
    response.json.return_value = {
        "jobs": [
            {
                "id": 999,
                "title": "AI Engineer",
                "location": {"name": location},
                "content": "<p>Python machine learning</p>",
                "absolute_url": "https://example.com/jobs/999",
            }
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

    assert bool(jobs) is expected, (
        f"Unexpected US location filtering result for {location}"
    )

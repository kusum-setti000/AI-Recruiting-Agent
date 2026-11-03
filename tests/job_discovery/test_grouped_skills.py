from unittest.mock import Mock, patch

from app.integrations.job_discovery.greenhouse import GreenhouseProvider
from app.integrations.job_discovery.models import CandidateJobProfile


def test_grouped_resume_skills_match_individual_job_skills():
    profile = CandidateJobProfile(
        target_titles=["Senior AI/ML Engineer"],
        skills=[
            "Python, SQL, Shell scripting",
            "LangChain, LangGraph, LangSmith",
        ],
        location="United States",
    )

    mock_response = Mock()
    mock_response.json.return_value = {
        "jobs": [
            {
                "id": 123,
                "title": "Agentic AI Engineer",
                "location": {"name": "Remote - United States"},
                "content": (
                    "Build agent workflows using "
                    "Python and LangGraph."
                ),
                "absolute_url": (
                    "https://job-boards.greenhouse.io/"
                    "example/jobs/123"
                ),
            }
        ]
    }

    provider = GreenhouseProvider(board_tokens=["example"])

    with patch(
        "app.integrations.job_discovery.greenhouse.requests.get",
        return_value=mock_response,
    ):
        jobs = provider.search(profile)

    assert len(jobs) == 1
    assert jobs[0].title == "Agentic AI Engineer"

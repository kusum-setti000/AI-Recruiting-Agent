from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)
from app.integrations.job_discovery.service import JobDiscoveryService


class FakeProvider:
    def search(self, profile):
        return [
            DiscoveredJob(
                source="greenhouse",
                external_id="1",
                title="Compliance Analyst",
                company="example",
                description="Python",
                job_url="https://example.com/jobs/1",
            ),
            DiscoveredJob(
                source="greenhouse",
                external_id="2",
                title="Senior AI Engineer",
                company="example",
                description="Python and Machine Learning",
                job_url="https://example.com/jobs/2",
            ),
        ]


def test_discovery_results_sorted_by_match_score():
    profile = CandidateJobProfile(
        target_titles=["Senior AI Engineer"],
        skills=["Python", "Machine Learning"],
    )

    result = JobDiscoveryService(
        providers=[FakeProvider()]
    ).search(profile)

    assert result.total_found == 2
    assert result.new_jobs == 2

    assert result.jobs[0].title == "Senior AI Engineer"
    assert result.jobs[1].title == "Compliance Analyst"

    assert result.jobs[0].match_score > result.jobs[1].match_score

    assert all(
        job.match_score is not None
        and 0 <= job.match_score <= 100
        for job in result.jobs
    )

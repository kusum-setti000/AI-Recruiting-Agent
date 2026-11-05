from unittest.mock import Mock

from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)
from app.integrations.job_discovery.service import JobDiscoveryService


def test_discovery_service_deduplicates_jobs():
    job = DiscoveredJob(
        source="greenhouse",
        external_id="123",
        title="Python Developer",
        company="Example",
        job_url="https://example.com/jobs/123",
    )

    provider1 = Mock()
    provider1.search.return_value = [job]

    provider2 = Mock()
    provider2.search.return_value = [job]

    service = JobDiscoveryService(
        providers=[provider1, provider2]
    )

    result = service.search(
        CandidateJobProfile(skills=["Python"])
    )

    assert result.total_found == 1
    assert result.new_jobs == 1
    assert len(result.jobs) == 1


def test_discovery_service_with_no_providers():
    service = JobDiscoveryService(providers=[])

    result = service.search(CandidateJobProfile())

    assert result.total_found == 0
    assert result.jobs == []

def test_discovery_service_preserves_distinct_greenhouse_jobs():
    first = DiscoveredJob(
        source="greenhouse",
        external_id="1001",
        title="AI Engineer",
        company="mongodb",
        job_url="https://www.mongodb.com/careers/job/?gh_jid=1001",
    )
    second = DiscoveredJob(
        source="greenhouse",
        external_id="1002",
        title="ML Engineer",
        company="mongodb",
        job_url="https://www.mongodb.com/careers/job/?gh_jid=1002",
    )

    provider = Mock()
    provider.search.return_value = [first, second]

    result = JobDiscoveryService(
        providers=[provider]
    ).search(CandidateJobProfile())

    assert result.total_found == 2
    assert {job.external_id for job in result.jobs} == {"1001", "1002"}

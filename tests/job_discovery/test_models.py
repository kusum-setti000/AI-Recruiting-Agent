from datetime import timezone

import pytest
from pydantic import ValidationError

from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
    JobDiscoveryResult,
)


def test_candidate_profile_defaults():
    profile = CandidateJobProfile()
    assert profile.target_titles == []
    assert profile.skills == []
    assert profile.remote_only is False


def test_discovered_job_creation():
    job = DiscoveredJob(
        source="adzuna",
        external_id="123",
        title="Python Developer",
        company="Example Company",
        job_url="https://example.com/jobs/123",
    )
    assert job.title == "Python Developer"
    assert job.discovered_at.tzinfo == timezone.utc


def test_job_requires_valid_url():
    with pytest.raises(ValidationError):
        DiscoveredJob(
            source="adzuna",
            external_id="123",
            title="Python Developer",
            company="Example Company",
            job_url="invalid-url",
        )


def test_discovery_result_defaults():
    result = JobDiscoveryResult()
    assert result.jobs == []
    assert result.total_found == 0
    assert result.new_jobs == 0

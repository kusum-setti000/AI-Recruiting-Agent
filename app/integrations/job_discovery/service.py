"""Combine job discovery providers and deduplicate results."""

from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    JobDiscoveryResult,
)
from app.integrations.job_discovery.greenhouse import GreenhouseProvider


class JobDiscoveryService:
    def __init__(self, providers=None):
        self.providers = (
            [GreenhouseProvider()]
            if providers is None
            else providers
        )

    def search(self, profile: CandidateJobProfile) -> JobDiscoveryResult:
        jobs = []
        seen = set()

        for provider in self.providers:
            provider_jobs = provider.search(profile)

            for job in provider_jobs:
                key = str(job.job_url).split("?")[0].rstrip("/").lower()

                if key in seen:
                    continue

                seen.add(key)
                jobs.append(job)

        return JobDiscoveryResult(
            jobs=jobs,
            total_found=len(jobs),
            new_jobs=len(jobs),
        )

"""Combine job discovery providers and deduplicate results."""

from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    JobDiscoveryResult,
)
from app.integrations.job_discovery.greenhouse import GreenhouseProvider


class JobDiscoveryService:
    def __init__(self, providers=None):
        self.providers = (
            [GreenhouseProvider(board_tokens=[
                "greenhouse",
                "datadog",
                "cloudflare",
                "figma",
                "databricks",
                "mongodb",
                "elastic",
                "stripe",
                "reddit",
            ])]
            if providers is None
            else providers
        )

    def search(self, profile: CandidateJobProfile) -> JobDiscoveryResult:
        jobs = []
        seen = set()

        for provider in self.providers:
            provider_jobs = provider.search(profile)

            for job in provider_jobs:
                # Greenhouse job IDs are unique within a company board.
                # Do not strip URL query parameters: some companies
                # identify individual jobs using gh_jid.
                if job.source == "greenhouse" and job.external_id:
                    key = (
                        job.source.lower(),
                        job.company.lower(),
                        str(job.external_id),
                    )
                else:
                    key = (
                        job.source.lower(),
                        str(job.job_url).rstrip("/").lower(),
                    )

                if key in seen:
                    continue

                seen.add(key)
                jobs.append(job)

        return JobDiscoveryResult(
            jobs=jobs,
            total_found=len(jobs),
            new_jobs=len(jobs),
        )

"""Adapter for LinkedIn-sourced TheirStack jobs."""

import os
from urllib.parse import urlparse

from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)
from app.integrations.job_discovery.linkedin_provider import (
    search_linkedin_jobs,
)


class TheirStackProvider:
    def __init__(self, limit=5):
        if not 1 <= limit <= 10:
            raise ValueError("Limit must be between 1 and 10")
        self.limit = limit

    def search(self, profile: CandidateJobProfile):
        if not os.getenv("THEIRSTACK_API_KEY"):
            raise RuntimeError("THEIRSTACK_API_KEY is missing")

        titles = [
            title.strip()
            for title in profile.target_titles
            if title.strip()
        ][:5]

        if not titles:
            raise ValueError(
                "Resume target titles are required for "
                "personalized TheirStack discovery."
            )

        raw_jobs = search_linkedin_jobs(
            title=titles,
            limit=self.limit,
        )

        jobs = []

        for item in raw_jobs:
            url = str(item.get("job_url") or "").strip()
            parsed = urlparse(url)

            if (
                parsed.scheme not in ("http", "https")
                or not parsed.hostname
            ):
                continue

            title_value = str(item.get("title") or "").strip()
            company = str(item.get("company") or "").strip()

            if not title_value:
                continue

            location = str(item.get("location") or "").strip()

            if profile.remote_only and not any(
                term in location.lower()
                for term in ("remote", "anywhere", "work from home")
            ):
                continue

            if profile.location:
                requested = profile.location.strip().lower()
                if requested not in ("us", "usa", "united states"):
                    if requested not in location.lower():
                        continue

            jobs.append(
                DiscoveredJob(
                    source="linkedin_via_theirstack",
                    external_id=str(
                        item.get("external_id") or url
                    ),
                    title=title_value,
                    company=company or "Unknown company",
                    location=location or None,
                    description=item.get("description") or None,
                    job_url=url,
                )
            )

        return jobs

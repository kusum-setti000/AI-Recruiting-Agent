import os

import requests

from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)


class AdzunaProvider:
    BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"

    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")

    def search(self, profile: CandidateJobProfile) -> list[DiscoveredJob]:
        if not self.app_id or not self.app_key:
            raise ValueError("ADZUNA_APP_ID and ADZUNA_APP_KEY are required")

        keywords = " ".join(profile.target_titles[:1] or profile.skills[:3])

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": keywords,
            "results_per_page": 20,
            "content-type": "application/json",
        }

        if profile.location:
            params["where"] = profile.location

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=20,
        )
        response.raise_for_status()

        jobs = []

        for item in response.json().get("results", []):
            jobs.append(
                DiscoveredJob(
                    source="adzuna",
                    external_id=str(item["id"]),
                    title=item["title"],
                    company=item.get("company", {}).get("display_name", "Unknown"),
                    location=item.get("location", {}).get("display_name"),
                    description=item.get("description"),
                    job_url=item["redirect_url"],
                )
            )

        return jobs

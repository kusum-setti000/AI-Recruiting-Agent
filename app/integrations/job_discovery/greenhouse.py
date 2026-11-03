"""Greenhouse public job-board integration."""

import re
from html import unescape

import requests

from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)


class GreenhouseProvider:
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, board_tokens=None):
        self.board_tokens = (
            ["greenhouse"] if board_tokens is None else board_tokens
        )

    def search(self, profile: CandidateJobProfile):
        jobs = []
        seen = set()

        keywords = [
            value.strip().lower()
            for value in profile.target_titles + profile.skills
            if value.strip()
        ]

        for token in self.board_tokens:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", token):
                raise ValueError("Invalid Greenhouse board token")

            response = requests.get(
                f"{self.BASE_URL}/{token}/jobs",
                params={"content": "true"},
                timeout=20,
            )
            response.raise_for_status()

            for item in response.json().get("jobs", []):
                title = item.get("title") or ""
                location = (item.get("location") or {}).get("name") or ""
                description = re.sub(
                    r"<[^>]+>",
                    " ",
                    unescape(item.get("content") or ""),
                )

                searchable = f"{title} {description}".lower()

                if keywords and not any(
                    keyword in searchable for keyword in keywords
                ):
                    continue

                if profile.remote_only:
                    if not any(
                        word in location.lower()
                        for word in ["remote", "anywhere", "work from home"]
                    ):
                        continue

                if profile.location and not profile.remote_only:
                    requested = profile.location.lower()
                    location_lower = location.lower()

                    if not (
                        requested in location_lower
                        or "anywhere in the united states" in location_lower
                        or "remote" in location_lower
                    ):
                        continue

                external_id = str(item["id"])
                identifier = (token, external_id)

                if identifier in seen:
                    continue

                seen.add(identifier)

                jobs.append(
                    DiscoveredJob(
                        source="greenhouse",
                        external_id=external_id,
                        title=title,
                        company=token,
                        location=location or None,
                        description=description.strip() or None,
                        job_url=item["absolute_url"],
                    )
                )

        return jobs

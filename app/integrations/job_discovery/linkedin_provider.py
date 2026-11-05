"""LinkedIn-sourced job discovery using TheirStack."""

import os
import requests

API_URL = "https://api.theirstack.com/v1/jobs/search"


def search_linkedin_jobs(
    title="Machine Learning Engineer",
    limit=5,
):
    api_key = os.getenv("THEIRSTACK_API_KEY")

    if not api_key:
        raise RuntimeError("THEIRSTACK_API_KEY is missing.")

    if not 1 <= limit <= 10:
        raise ValueError("Limit must be between 1 and 10.")

    payload = {
        "job_title_pattern_or": (
            list(dict.fromkeys(
                t.strip() for t in title
                if isinstance(t, str) and t.strip()
            ))[:5]
            if isinstance(title, (list, tuple))
            else [title]
        ),
        "url_domain_or": ["linkedin.com"],
        "posted_at_max_age_days": 30,
        "limit": limit,
        "page": 0,
    }

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=45,
    )

    if not response.ok:
        raise RuntimeError(
            f"TheirStack API returned HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    data = response.json()
    jobs = data.get("data", [])

    results = []

    for job in jobs:
        results.append({
            "external_id": str(job.get("id") or ""),
            "title": job.get("job_title") or "",
            "company": job.get("company") or "",
            "description": job.get("description") or "",
            "location": job.get("location") or "",
            "job_url": job.get("url") or job.get("source_url") or "",
            "source_url": job.get("source_url") or "",
            "source": "linkedin_via_theirstack",
        })

    return results

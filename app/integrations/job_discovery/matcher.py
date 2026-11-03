"""Deterministic resume-to-job relevance scoring."""

import re

from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)


def normalize(text: str) -> str:
    """Normalize text for consistent matching."""
    return " ".join(
        re.findall(r"[a-z0-9+#.]+", text.lower())
    )


def phrase_matches(phrase: str, text: str) -> bool:
    """Match a complete normalized phrase, not a substring."""
    normalized_phrase = normalize(phrase)
    normalized_text = normalize(text)

    if not normalized_phrase:
        return False

    return (
        f" {normalized_phrase} "
        in f" {normalized_text} "
    )


def calculate_match_score(
    profile: CandidateJobProfile,
    job: DiscoveredJob,
) -> int:
    """Calculate a relevance score from 0 to 100."""

    title = job.title or ""
    description = job.description or ""

    target_titles = [
        value for value in profile.target_titles
        if normalize(value)
    ]

    skills = [
        value for value in profile.skills
        if normalize(value)
    ]

    title_score = 0.0

    if target_titles:
        title_score = max(
            (
                1.0
                if normalize(target) == normalize(title)
                else 0.8
                if phrase_matches(target, title)
                or phrase_matches(title, target)
                else 0.0
            )
            for target in target_titles
        )

    skill_score = 0.0

    if skills:
        matched = sum(
            1 for skill in skills
            if phrase_matches(
                skill,
                f"{title} {description}",
            )
        )

        skill_score = matched / len(skills)

    if target_titles and skills:
        score = 0.7 * title_score + 0.3 * skill_score
    elif target_titles:
        score = title_score
    elif skills:
        score = skill_score
    else:
        score = 0.0

    return round(score * 100)

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
    """Match complete normalized phrases."""
    normalized_phrase = normalize(phrase)
    normalized_text = normalize(text)

    if not normalized_phrase:
        return False

    return (
        f" {normalized_phrase} "
        in f" {normalized_text} "
    )


def title_tokens(title: str) -> set[str]:
    """Normalize common AI/ML terminology in job titles."""
    text = title.lower()

    text = re.sub(
        r"\bmachine[\s-]+learning\b",
        " ml ",
        text,
    )
    text = re.sub(
        r"\bartificial[\s-]+intelligence\b",
        " ai ",
        text,
    )
    text = re.sub(r"\bgenai\b", " ai ", text)
    text = re.sub(r"\bgenerative\s+ai\b", " ai ", text)
    text = re.sub(r"\bagentic\s+ai\b", " ai ", text)
    text = re.sub(r"\bmlops\b", " ml ", text)

    tokens = set(re.findall(r"[a-z0-9]+", text))

    ignored = {
        "senior", "staff", "principal", "lead",
        "junior", "the", "and", "of", "for",
    }

    return tokens - ignored


def title_similarity(target: str, actual: str) -> float:
    """Measure title overlap without rewarding generic partial titles."""
    target_set = title_tokens(target)
    actual_set = title_tokens(actual)

    if not target_set or not actual_set:
        return 0.0

    if target_set == actual_set:
        return 1.0

    intersection = target_set & actual_set

    if not intersection:
        return 0.0

    return len(intersection) / len(
        target_set | actual_set
    )


def calculate_match_score(
    profile: CandidateJobProfile,
    job: DiscoveredJob,
) -> int:
    """Calculate a deterministic relevance score from 0 to 100."""
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
            title_similarity(target, title)
            for target in target_titles
        )

    skill_score = 0.0

    if skills:
        matched = sum(
            1
            for skill in skills
            if phrase_matches(
                skill, f"{title} {description}"
            )
        )

        # Cap the skill evidence needed for a full score.
        # This prevents very long resumes from diluting matches.
        required_matches = min(len(skills), 8)
        skill_score = min(
            matched / required_matches, 1.0
        )

    if target_titles and skills:
        score = (
            0.65 * title_score
            + 0.35 * skill_score
        )
    elif target_titles:
        score = title_score
    elif skills:
        score = skill_score
    else:
        score = 0.0

    return max(0, min(100, round(score * 100)))

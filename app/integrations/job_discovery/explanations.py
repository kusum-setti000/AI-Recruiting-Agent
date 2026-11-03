"""Deterministic explanations for resume-to-job matching."""

from app.integrations.job_discovery.matcher import (
    experience_adjustment,
    extract_required_experience,
    normalize,
    phrase_matches,
    title_similarity,
)
from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
    MatchExplanation,
)


def explain_match(
    profile: CandidateJobProfile,
    job: DiscoveredJob,
) -> MatchExplanation:
    """Explain evidence used by the deterministic matcher."""
    title = job.title or ""
    description = job.description or ""
    searchable_text = f"{title} {description}"

    skills = list(dict.fromkeys(
        skill.strip()
        for group in profile.skills
        for skill in group.split(",")
        if normalize(skill)
    ))

    matched_skills = [
        skill for skill in skills
        if phrase_matches(skill, searchable_text)
    ]

    unmatched_skills = [
        skill for skill in skills
        if not phrase_matches(skill, searchable_text)
    ]

    title_scores = [
        title_similarity(target, title)
        for target in profile.target_titles
        if normalize(target)
    ]

    similarity = max(title_scores, default=0.0)

    required_years = extract_required_experience(description)
    candidate_years = profile.experience_years

    gap = (
        max(0.0, required_years - candidate_years)
        if required_years is not None and candidate_years is not None
        else 0.0
    )

    penalty = experience_adjustment(candidate_years, required_years)

    return MatchExplanation(
        matched_skills=matched_skills,
        unmatched_candidate_skills=unmatched_skills,
        title_similarity=similarity,
        candidate_experience_years=candidate_years,
        required_experience_years=required_years,
        experience_gap_years=gap,
        experience_penalty_points=round(penalty * 100),
    )

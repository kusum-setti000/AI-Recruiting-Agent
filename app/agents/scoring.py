
"""Deterministic candidate scoring rules for TalentFlow AI."""


def assessment_from_score(score: int) -> str:
    """Convert a candidate match score into an assessment band."""

    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("Match score must be an integer.")

    if not 0 <= score <= 100:
        raise ValueError("Match score must be between 0 and 100.")

    if score >= 85:
        return "Strong Match"

    if score >= 70:
        return "Potential Match"

    if score >= 50:
        return "Needs Human Review"

    return "Weak Match"

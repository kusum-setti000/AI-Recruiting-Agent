
from typing import Literal


AssessmentLabel = Literal[
    "Strong Match",
    "Potential Match",
    "Needs Human Review",
    "Weak Match",
]


def assessment_from_score(score: int) -> AssessmentLabel:
    """
    Convert a candidate match score into an assessment label.

    Score bands:
        85-100: Strong Match
        70-84: Potential Match
        50-69: Needs Human Review
        0-49: Weak Match
    """

    if isinstance(score, bool) or not isinstance(score, int):
        raise TypeError(
            "Match score must be an integer."
        )

    if not 0 <= score <= 100:
        raise ValueError(
            "Match score must be between 0 and 100."
        )

    if score >= 85:
        return "Strong Match"

    if score >= 70:
        return "Potential Match"

    if score >= 50:
        return "Needs Human Review"

    return "Weak Match"

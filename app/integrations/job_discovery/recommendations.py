"""Human-readable explanations of job relevance."""

from app.integrations.job_discovery.models import MatchExplanation


def build_recommendation(explanation: MatchExplanation) -> str:
    """Generate a concise, evidence-based job match summary."""
    parts = []

    if explanation.title_similarity >= 0.8:
        parts.append("The job title closely matches your target role.")
    elif explanation.title_similarity > 0:
        parts.append("The job title partially matches your target role.")
    else:
        parts.append("The job title does not match your target role.")

    if explanation.matched_skills:
        parts.append(
            "Matching skills: "
            + ", ".join(explanation.matched_skills)
            + "."
        )
    else:
        parts.append("No matching candidate skills were identified.")

    required = explanation.required_experience_years
    available = explanation.candidate_experience_years

    if required is not None and available is not None:
        if available >= required:
            parts.append(
                f"Your {available:g} years of experience meet "
                f"the stated {required:g}-year minimum."
            )
        else:
            parts.append(
                f"The posting requires {required:g} years of experience; "
                f"your profile lists {available:g}."
            )
    elif required is not None:
        parts.append(
            f"The posting requires {required:g} years of experience, "
            "but your experience is not specified."
        )
    else:
        parts.append(
            "No explicit minimum experience requirement was detected."
        )

    if explanation.unmatched_candidate_skills:
        parts.append(
            "Candidate skills not mentioned in the posting: "
            + ", ".join(explanation.unmatched_candidate_skills)
            + "."
        )

    return " ".join(parts)

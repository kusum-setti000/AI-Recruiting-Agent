"""Deterministic resume-to-job relevance scoring."""
import re

from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)


def normalize(text: str) -> str:
    """Normalize punctuation while preserving technical skill symbols."""
    tokens = re.findall(r"[a-z0-9+#.]+", text.lower())

    return " ".join(
        token.strip(".")
        for token in tokens
        if token.strip(".")
    )


SKILL_ALIASES = {
    "machine learning": ("ml",),
    "generative ai": ("genai",),
    "large language models": (
        "llm",
        "llms",
        "large language model",
    ),
    "retrieval augmented generation": ("rag",),
}


def phrase_matches(phrase: str, text: str) -> bool:
    """Match skills using bidirectional terminology aliases."""
    normalized_phrase = normalize(phrase)
    normalized_text = normalize(text)

    if not normalized_phrase:
        return False

    candidates = {normalized_phrase}

    for canonical, aliases in SKILL_ALIASES.items():
        equivalents = {
            normalize(canonical),
            *(normalize(alias) for alias in aliases),
        }

        if normalized_phrase in equivalents:
            candidates.update(equivalents)
            break

    return any(
        f" {candidate} " in f" {normalized_text} "
        for candidate in candidates
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



def extract_required_experience(description: str) -> float | None:
    """Extract explicit minimum years of experience."""
    patterns = (
        r"([0-9]+(?:[.][0-9]+)?)[ ]*[+][ ]*years? +of +experience",
        r"(?:minimum|min[.]?|at least) +([0-9]+(?:[.][0-9]+)?)[ ]+years? +of +experience",
        r"([0-9]+(?:[.][0-9]+)?)[ ]*(?:-|to)[ ]*[0-9]+(?:[.][0-9]+)?[ ]+years? +of +experience",
    )

    matches = [
        float(match.group(1))
        for pattern in patterns
        for match in re.finditer(pattern, description, re.IGNORECASE)
    ]

    return max(matches) if matches else None


def experience_adjustment(
    candidate_years: float | None,
    required_years: float | None,
) -> float:
    """Return a conservative score penalty for experience gaps."""
    if candidate_years is None or required_years is None:
        return 0.0

    gap = required_years - candidate_years

    if gap <= 0:
        return 0.0

    return min(0.20, gap * 0.04)


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
    skills = list(dict.fromkeys(
        skill.strip()
        for group in profile.skills
        for skill in group.split(",")
        if normalize(skill)
    ))

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

    required_years = extract_required_experience(description)

    penalty = experience_adjustment(
        profile.experience_years,
        required_years,
    )

    score = max(0.0, score - penalty)

    return max(0, min(100, round(score * 100)))

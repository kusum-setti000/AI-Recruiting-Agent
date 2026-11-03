from app.integrations.job_discovery.matcher import (
    calculate_match_score,
)
from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)


def make_job(title, description):
    return DiscoveredJob(
        source="greenhouse",
        external_id="test-1",
        title=title,
        company="example",
        location="Houston, TX",
        description=description,
        job_url="https://example.com/jobs/1",
    )


def test_exact_title_match_scores_higher():
    profile = CandidateJobProfile(
        target_titles=["Senior AI Engineer"],
        skills=["Python", "Machine Learning"],
    )

    exact = make_job(
        "Senior AI Engineer",
        "Python and Machine Learning",
    )

    unrelated = make_job(
        "Compliance Analyst",
        "Python and Machine Learning",
    )

    assert calculate_match_score(
        profile, exact
    ) > calculate_match_score(
        profile, unrelated
    )


def test_skill_overlap_increases_score():
    profile = CandidateJobProfile(
        target_titles=["AI Engineer"],
        skills=["Python", "LangChain", "FastAPI"],
    )

    strong = make_job(
        "AI Engineer",
        "Python LangChain FastAPI",
    )

    weak = make_job(
        "AI Engineer",
        "Python only",
    )

    assert calculate_match_score(
        profile, strong
    ) > calculate_match_score(
        profile, weak
    )


def test_score_stays_within_bounds():
    profile = CandidateJobProfile(
        target_titles=["ML Engineer"],
        skills=["Python"],
    )

    job = make_job(
        "ML Engineer",
        "Python",
    )

    score = calculate_match_score(profile, job)

    assert 0 <= score <= 100


def test_empty_profile_returns_zero():
    profile = CandidateJobProfile()

    job = make_job(
        "AI Engineer",
        "Python",
    )

    assert calculate_match_score(profile, job) == 0

import pytest

from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
    MatchExplanation,
)
from app.integrations.job_discovery.recommendations import build_recommendation
from app.integrations.job_discovery.service import JobDiscoveryService


def make_explanation(**overrides):
    values = {
        "matched_skills": ["Python", "Machine Learning"],
        "unmatched_candidate_skills": ["Kubernetes"],
        "title_similarity": 1.0,
        "candidate_experience_years": 6,
        "required_experience_years": 5,
        "experience_gap_years": 0,
        "experience_penalty_points": 0,
    }
    values.update(overrides)
    return MatchExplanation(**values)


def test_strong_title_match():
    summary = build_recommendation(make_explanation())
    assert "closely matches" in summary


def test_partial_title_match():
    summary = build_recommendation(
        make_explanation(title_similarity=0.5)
    )
    assert "partially matches" in summary


def test_no_title_match():
    summary = build_recommendation(
        make_explanation(title_similarity=0)
    )
    assert "does not match" in summary


def test_matched_skills():
    summary = build_recommendation(make_explanation())
    assert "Python, Machine Learning" in summary


def test_unmatched_candidate_skills():
    summary = build_recommendation(make_explanation())
    assert "Candidate skills not mentioned" in summary
    assert "Kubernetes" in summary


def test_qualified_experience():
    summary = build_recommendation(make_explanation())
    assert "meet the stated 5-year minimum" in summary


def test_experience_shortfall():
    summary = build_recommendation(
        make_explanation(candidate_experience_years=3)
    )
    assert "requires 5 years of experience" in summary


def test_missing_candidate_experience():
    summary = build_recommendation(
        make_explanation(candidate_experience_years=None)
    )
    assert "experience is not specified" in summary


def test_missing_job_experience_requirement():
    summary = build_recommendation(
        make_explanation(required_experience_years=None)
    )
    assert "No explicit minimum experience requirement" in summary


def test_service_includes_recommendation_in_api_model():
    profile = CandidateJobProfile(
        target_titles=["Machine Learning Engineer"],
        skills=["Python"],
        experience_years=6,
    )

    job = DiscoveredJob(
        source="greenhouse",
        external_id="recommendation-test",
        title="Machine Learning Engineer",
        company="Example",
        description="Python and ML. Minimum 5 years of experience.",
        job_url="https://example.com/jobs/recommendation-test",
    )

    class FakeProvider:
        def search(self, candidate_profile):
            return [job]

    result = JobDiscoveryService(
        providers=[FakeProvider()]
    ).search(profile)

    discovered = result.jobs[0]

    assert discovered.match_explanation is not None
    assert discovered.recommendation_summary is not None
    assert "Python" in discovered.recommendation_summary

    serialized = result.model_dump(mode="json")
    assert serialized["jobs"][0]["recommendation_summary"]

from app.integrations.job_discovery.explanations import explain_match
from app.integrations.job_discovery.matcher import calculate_match_score
from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)
from app.integrations.job_discovery.service import JobDiscoveryService


def make_profile(years=6):
    return CandidateJobProfile(
        target_titles=["Machine Learning Engineer"],
        skills=["Python", "Machine Learning", "Kubernetes"],
        experience_years=years,
    )


def make_job(description):
    return DiscoveredJob(
        source="greenhouse",
        external_id="explanation-test",
        title="Machine Learning Engineer",
        company="Example",
        description=description,
        job_url="https://example.com/jobs/explanation-test",
    )


def test_matched_and_unmatched_candidate_skills():
    job = make_job(
        "Python and ML development. Minimum 5 years of experience."
    )
    explanation = explain_match(make_profile(), job)

    assert explanation.matched_skills == ["Python", "Machine Learning"]
    assert explanation.unmatched_candidate_skills == ["Kubernetes"]


def test_title_similarity():
    job = make_job("Python and ML")
    explanation = explain_match(make_profile(), job)

    assert explanation.title_similarity == 1.0


def test_qualified_candidate_has_no_experience_gap():
    job = make_job("Minimum 5 years of experience.")
    explanation = explain_match(make_profile(6), job)

    assert explanation.required_experience_years == 5
    assert explanation.candidate_experience_years == 6
    assert explanation.experience_gap_years == 0
    assert explanation.experience_penalty_points == 0


def test_experience_gap_and_penalty():
    job = make_job("Minimum 8 years of experience.")
    explanation = explain_match(make_profile(6), job)

    assert explanation.experience_gap_years == 2
    assert explanation.experience_penalty_points == 8


def test_missing_experience_is_not_assumed():
    job = make_job("Python development.")
    explanation = explain_match(make_profile(None), job)

    assert explanation.required_experience_years is None
    assert explanation.experience_gap_years == 0
    assert explanation.experience_penalty_points == 0


def test_explanation_does_not_modify_match_score():
    profile = make_profile()
    job = make_job("Python and ML. Minimum 8 years of experience.")

    expected = calculate_match_score(profile, job)
    explain_match(profile, job)

    assert calculate_match_score(profile, job) == expected


def test_service_attaches_explanation():
    profile = make_profile()
    job = make_job("Python and ML. Minimum 5 years of experience.")

    class FakeProvider:
        def search(self, candidate_profile):
            return [job]

    result = JobDiscoveryService(providers=[FakeProvider()]).search(profile)

    assert result.total_found == 1
    assert result.jobs[0].match_explanation is not None
    assert result.jobs[0].match_score is not None
    assert "Python" in result.jobs[0].match_explanation.matched_skills

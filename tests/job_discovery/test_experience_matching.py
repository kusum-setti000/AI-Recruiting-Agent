import pytest

from app.integrations.job_discovery.matcher import (
    calculate_match_score,
    extract_required_experience,
)
from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)


@pytest.mark.parametrize(
    "description,expected",
    [
        ("Requires 8+ years of experience.", 8),
        ("Minimum 5 years of experience.", 5),
        ("At least 7 years of experience.", 7),
        ("Requires 5-8 years of experience.", 5),
        ("Experience with Python and AWS.", None),
        ("Python 3.12 and 8 APIs.", None),
    ],
)
def test_experience_extraction(description, expected):
    assert extract_required_experience(description) == expected


def make_job(description):
    return DiscoveredJob(
        source="greenhouse",
        external_id="experience-test",
        title="Machine Learning Engineer",
        company="Example",
        location="United States",
        description=description,
        job_url="https://example.com/job",
    )


def make_profile(years):
    return CandidateJobProfile(
        target_titles=["Machine Learning Engineer"],
        skills=["Python"],
        experience_years=years,
    )


def test_qualified_candidate_has_no_penalty():
    job = make_job("Skills: Python and AWS. Minimum 8 years of experience.")
    assert calculate_match_score(make_profile(10), job) == 100


def test_small_experience_gap_reduces_score():
    job = make_job("Skills: Python and AWS. Minimum 12 years of experience.")
    assert calculate_match_score(make_profile(10), job) == 92


def test_large_experience_gap_has_capped_penalty():
    job = make_job("Skills: Python and AWS. Minimum 8 years of experience.")
    assert calculate_match_score(make_profile(3), job) == 80


def test_missing_job_requirement_has_no_penalty():
    job = make_job("Build ML systems using Python and AWS.")
    assert calculate_match_score(make_profile(3), job) == 100


def test_missing_candidate_experience_has_no_penalty():
    job = make_job("Skills: Python and AWS. Minimum 8 years of experience.")
    assert calculate_match_score(make_profile(None), job) == 100

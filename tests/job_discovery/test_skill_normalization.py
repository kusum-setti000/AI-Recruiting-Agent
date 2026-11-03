from app.integrations.job_discovery.matcher import calculate_match_score
from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)


def make_job():
    return DiscoveredJob(
        source="greenhouse",
        external_id="skill-normalization-1",
        title="Agentic AI Engineer",
        company="example",
        location="United States",
        description=(
            "Build AI agents using Python, LangChain, "
            "LangGraph, and PyTorch."
        ),
        job_url="https://example.com/jobs/skill-normalization-1",
    )


def test_grouped_and_individual_skills_produce_same_score():
    grouped_profile = CandidateJobProfile(
        target_titles=["Generative AI Engineer"],
        skills=["Python, LangChain, LangGraph, PyTorch"],
    )

    individual_profile = CandidateJobProfile(
        target_titles=["Generative AI Engineer"],
        skills=[
            "Python",
            "LangChain",
            "LangGraph",
            "PyTorch",
        ],
    )

    job = make_job()

    grouped_score = calculate_match_score(grouped_profile, job)
    individual_score = calculate_match_score(individual_profile, job)

    assert grouped_score == individual_score

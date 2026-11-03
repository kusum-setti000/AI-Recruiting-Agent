from app.integrations.job_discovery.matcher import calculate_match_score
from app.integrations.job_discovery.models import (
    CandidateJobProfile,
    DiscoveredJob,
)


def make_job(title, description):
    return DiscoveredJob(
        source="greenhouse",
        external_id=title,
        title=title,
        company="test",
        location="United States",
        description=description,
        job_url="https://example.com/jobs/test",
    )


def test_agentic_ai_ranks_above_payments_architect():
    profile = CandidateJobProfile(
        target_titles=[
            "Senior AI/ML Engineer",
            "Generative AI Engineer",
            "AI/ML Solutions Architect",
        ],
        skills=[
            "Python",
            "LangChain",
            "LangGraph",
            "Generative AI",
            "Machine learning",
            "MLOps",
        ],
    )

    ai_job = make_job(
        "Agentic AI Engineer",
        "Build LLM agents using Python, LangChain, LangGraph and Generative AI.",
    )

    payments_job = make_job(
        "Solutions Architect",
        "Design payment solutions and integrate billing APIs using Python.",
    )

    assert calculate_match_score(
        profile, ai_job
    ) > calculate_match_score(
        profile, payments_job
    )


def test_machine_learning_related_titles_receive_credit():
    profile = CandidateJobProfile(
        target_titles=["Machine Learning Platform Engineer"],
        skills=["Python", "MLOps", "Kubernetes"],
    )

    related = make_job(
        "Senior Machine Learning Systems Engineer",
        "Develop ML infrastructure using Python, MLOps and Kubernetes.",
    )

    unrelated = make_job(
        "Technical Account Manager",
        "Support customer accounts using Python.",
    )

    assert calculate_match_score(
        profile, related
    ) > calculate_match_score(
        profile, unrelated
    )

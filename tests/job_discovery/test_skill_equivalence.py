import pytest

from app.integrations.job_discovery.matcher import phrase_matches


@pytest.mark.parametrize(
    "resume_skill,job_text",
    [
        ("Machine Learning", "Experience building ML models"),
        ("Generative AI", "Develop GenAI applications"),
        ("Large Language Models", "Work with LLMs"),
        ("Retrieval-Augmented Generation", "Build RAG pipelines"),
        ("Python", "Strong Python programming skills"),
    ],
)
def test_equivalent_skills_match(resume_skill, job_text):
    assert phrase_matches(resume_skill, job_text)


def test_unrelated_skills_do_not_match():
    assert not phrase_matches(
        "Java",
        "Experience with JavaScript and TypeScript",
    )

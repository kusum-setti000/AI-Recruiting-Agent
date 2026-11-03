import pytest

from app.integrations.job_discovery.matcher import phrase_matches


@pytest.mark.parametrize(
    "resume_skill,job_text",
    [
        ("ML", "Experience in Machine Learning"),
        ("GenAI", "Build Generative AI applications"),
        ("LLMs", "Develop Large Language Models"),
        ("RAG", "Retrieval-Augmented Generation pipelines"),
        ("Machine Learning", "Experience with ML"),
        ("Generative AI", "Experience with GenAI"),
    ],
)
def test_bidirectional_skill_aliases(resume_skill, job_text):
    assert phrase_matches(resume_skill, job_text)


@pytest.mark.parametrize(
    "resume_skill,job_text",
    [
        ("Java", "JavaScript development"),
        ("ML", "HTML development"),
        ("RAG", "Ragtime music"),
        ("AI", "Paid vacation"),
    ],
)
def test_skill_aliases_avoid_false_positives(resume_skill, job_text):
    assert not phrase_matches(resume_skill, job_text)

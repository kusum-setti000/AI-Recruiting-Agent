import pytest

from app.integrations.job_discovery.matcher import (
    normalize,
    phrase_matches,
)


@pytest.mark.parametrize(
    "description",
    [
        "Experience with Python.",
        "Python, Java, SQL",
        "Python/SQL development",
        "Python-based applications",
        "Python: required",
        "(Python)",
    ],
)
def test_python_matches_punctuation(description):
    assert phrase_matches("Python", description)


@pytest.mark.parametrize(
    "description",
    [
        "Pythonista developer",
        "Pythonic code",
        "CPython runtime",
        "No relevant experience",
    ],
)
def test_python_does_not_match_partial_words(description):
    assert not phrase_matches("Python", description)


@pytest.mark.parametrize(
    "skill,description",
    [
        ("C++", "Experience with C++."),
        ("C#", "Experience with C#, Java"),
        (".NET", "Experience with .NET."),
        ("SQL", "SQL, Python and Java"),
        ("machine learning", "ML-based systems"),
        ("GenAI", "Generative AI applications"),
        ("RAG", "Retrieval Augmented Generation systems"),
    ],
)
def test_technical_skills_and_aliases(skill, description):
    assert phrase_matches(skill, description)


def test_normalize_removes_trailing_period():
    assert normalize("Python.") == "python"

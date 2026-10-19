
"""Integration tests for the TalentFlow screening workflow."""

import pytest

from app.agents.graph import create_screening_graph, run_screening_graph
from app.agents.document_loader import ResumeValidationError


def test_graph_compiles():
    assert create_screening_graph() is not None


def test_graph_is_cached():
    assert create_screening_graph() is create_screening_graph()


def test_invalid_resume_bytes():
    with pytest.raises(TypeError):
        run_screening_graph(
            job_title="Data Scientist",
            job_description="Python and machine learning",
            resume_filename="resume.pdf",
            resume_bytes="invalid",
        )


def test_graph_structure():
    graph = create_screening_graph()
    nodes = graph.get_graph().nodes

    expected = {
        "validate_alignment",
        "load_resume",
        "analyze_candidate",
        "validate_output",
    }

    assert expected.issubset(nodes.keys())


"""LangGraph workflow for TalentFlow AI candidate screening."""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    ScreeningState,
    analyze_candidate_node,
    load_resume_node,
    route_after_alignment,
    validate_alignment_node,
    validate_output_node,
)
from app.agents.observability import get_tracing_context


@lru_cache(maxsize=1)
def create_screening_graph():
    """Build and compile the candidate screening workflow."""
    workflow = StateGraph(ScreeningState)

    workflow.add_node("validate_alignment", validate_alignment_node)
    workflow.add_node("load_resume", load_resume_node)
    workflow.add_node("analyze_candidate", analyze_candidate_node)
    workflow.add_node("validate_output", validate_output_node)

    workflow.add_edge(START, "validate_alignment")

    workflow.add_conditional_edges(
        "validate_alignment",
        route_after_alignment,
        {
            "load_resume": "load_resume",
            "stop": END,
        },
    )

    workflow.add_edge("load_resume", "analyze_candidate")
    workflow.add_edge("analyze_candidate", "validate_output")
    workflow.add_edge("validate_output", END)

    return workflow.compile()


def run_screening_graph(
    job_title: str,
    job_description: str,
    resume_filename: str,
    resume_bytes: bytes,
) -> dict:
    """Execute candidate screening and return UI-compatible results."""
    if not isinstance(resume_bytes, bytes):
        raise TypeError("resume_bytes must be bytes.")

    initial_state: ScreeningState = {
        "job_title": job_title,
        "job_description": job_description,
        "resume_filename": resume_filename,
        "resume_bytes": resume_bytes,
    }

    graph = create_screening_graph()

    with get_tracing_context():
        final_state = graph.invoke(initial_state)

    return {
        "candidate_resume": resume_filename,
        "job_title": job_title.strip(),
        "job_alignment": final_state.get("job_alignment"),
        "ai_analysis": final_state.get("ai_analysis"),
    }

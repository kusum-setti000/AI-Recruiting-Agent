
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.models.schemas import CandidateAnalysis, JobAlignment
from app.prompts.screening_prompt import build_screening_prompt
from app.services.llm_service import (
    analyze_with_llm,
    validate_job_alignment,
)


# ==========================================================
# 1. LANGGRAPH STATE
# ==========================================================

class ScreeningState(TypedDict, total=False):
    job_title: str
    job_description: str
    resume_text: str

    job_alignment: dict[str, Any]
    screening_prompt: str
    ai_analysis: dict[str, Any]

    validation_error: str


# ==========================================================
# 2. NODE: VALIDATE JOB ALIGNMENT
# ==========================================================

def validate_alignment_node(state: ScreeningState):
    existing_alignment = state.get("job_alignment")

    if existing_alignment is not None:
        if existing_alignment.get("status") == "aligned":
            logger.info(
                "[LangGraph] Reusing prevalidated job alignment. "
                "Skipping duplicate LLM call."
            )
            return {"job_alignment": existing_alignment}

    logger.info(
        "[LangGraph] Validating job alignment using LangChain."
    )

    alignment = validate_job_alignment(
        job_title=state["job_title"],
        job_description=state["job_description"],
    )

    return {"job_alignment": alignment.model_dump()}
# ==========================================================
# 3. CONDITIONAL ROUTING
# ==========================================================

def route_after_alignment(
    state: ScreeningState,
) -> str:

    alignment = state["job_alignment"]

    if alignment["status"] == "aligned":
        return "continue"

    return "stop"


# ==========================================================
# 4. NODE: BUILD SCREENING PROMPT
# ==========================================================

def build_prompt_node(
    state: ScreeningState,
) -> dict:

    prompt = build_screening_prompt(
        resume_text=state["resume_text"],
        job_description=state["job_description"],
        job_title=state["job_title"],
    )

    return {
        "screening_prompt": prompt,
    }


# ==========================================================
# 5. NODE: ANALYZE CANDIDATE
# ==========================================================

def analyze_candidate_node(
    state: ScreeningState,
) -> dict:

    analysis: CandidateAnalysis = analyze_with_llm(
        state["screening_prompt"]
    )

    return {
        "ai_analysis": analysis.model_dump(),
    }


# ==========================================================
# 6. NODE: VALIDATE OUTPUT
# ==========================================================

def validate_output_node(
    state: ScreeningState,
) -> dict:

    analysis = state["ai_analysis"]

    score = analysis["match_score"]

    if not isinstance(score, int) or not 0 <= score <= 100:
        raise ValueError(
            "AI screening score must be an integer "
            "between 0 and 100."
        )

    if score >= 85:
        expected_assessment = "Strong Match"
    elif score >= 70:
        expected_assessment = "Potential Match"
    elif score >= 50:
        expected_assessment = "Needs Human Review"
    else:
        expected_assessment = "Weak Match"

    if analysis["overall_assessment"] != expected_assessment:
        raise ValueError(
            "Screening assessment is inconsistent "
            "with the match score."
        )

    return {}


# ==========================================================
# 7. BUILD LANGGRAPH WORKFLOW
# ==========================================================

workflow = StateGraph(ScreeningState)

workflow.add_node(
    "validate_alignment",
    validate_alignment_node,
)

workflow.add_node(
    "build_prompt",
    build_prompt_node,
)

workflow.add_node(
    "analyze_candidate",
    analyze_candidate_node,
)

workflow.add_node(
    "validate_output",
    validate_output_node,
)

workflow.add_edge(
    START,
    "validate_alignment",
)

workflow.add_conditional_edges(
    "validate_alignment",
    route_after_alignment,
    {
        "continue": "build_prompt",
        "stop": END,
    },
)

workflow.add_edge(
    "build_prompt",
    "analyze_candidate",
)

workflow.add_edge(
    "analyze_candidate",
    "validate_output",
)

workflow.add_edge(
    "validate_output",
    END,
)

screening_graph = workflow.compile()


# ==========================================================
# 8. PUBLIC WORKFLOW FUNCTION
# ==========================================================



@traceable(
    name="TalentFlow Candidate Screening",
    run_type="chain",
    project_name="TalentFlow-AI",
)
def run_screening_graph(
    job_title: str,
    job_description: str,
    resume_text: str,
    prevalidated_alignment: dict | None = None,
):
    """
    Execute the LangGraph candidate screening workflow.

    Reuse prevalidated job alignment when available.
    """

    initial_state = {
        "job_title": job_title,
        "job_description": job_description,
        "resume_text": resume_text,
    }

    if prevalidated_alignment is not None:
        initial_state["job_alignment"] = prevalidated_alignment

    return screening_graph.invoke(initial_state)

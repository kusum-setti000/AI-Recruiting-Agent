
import logging
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.core.scoring import assessment_from_score
from app.models.schemas import CandidateAnalysis
from app.prompts.screening_prompt import build_screening_prompt
from app.services.llm_service import (
    analyze_with_llm,
    validate_job_alignment,
)


logger = logging.getLogger(__name__)


# --------------------------------------------------
# 1. LangGraph state
# --------------------------------------------------

class ScreeningState(TypedDict, total=False):
    job_title: str
    job_description: str
    resume_text: str
    job_alignment: dict[str, Any]
    screening_prompt: str
    ai_analysis: dict[str, Any]


# --------------------------------------------------
# 2. Validate job alignment
# --------------------------------------------------

def validate_alignment_node(
    state: ScreeningState,
) -> dict[str, Any]:

    existing_alignment = state.get("job_alignment")

    if (
        existing_alignment is not None
        and existing_alignment.get("status") == "aligned"
    ):
        logger.info(
            "Reusing prevalidated job alignment."
        )
        return {"job_alignment": existing_alignment}

    logger.info("Validating job alignment.")

    alignment = validate_job_alignment(
        job_title=state["job_title"],
        job_description=state["job_description"],
    )

    return {"job_alignment": alignment.model_dump()}


# --------------------------------------------------
# 3. Conditional routing
# --------------------------------------------------

def route_after_alignment(
    state: ScreeningState,
) -> str:

    alignment = state["job_alignment"]

    if alignment["status"] == "aligned":
        return "continue"

    return "stop"


# --------------------------------------------------
# 4. Build screening prompt
# --------------------------------------------------

def build_prompt_node(
    state: ScreeningState,
) -> dict[str, str]:

    prompt = build_screening_prompt(
        resume_text=state["resume_text"],
        job_description=state["job_description"],
        job_title=state["job_title"],
    )

    return {"screening_prompt": prompt}


# --------------------------------------------------
# 5. Analyze candidate
# --------------------------------------------------

def analyze_candidate_node(
    state: ScreeningState,
) -> dict[str, Any]:

    analysis: CandidateAnalysis = analyze_with_llm(
        state["screening_prompt"]
    )

    return {"ai_analysis": analysis.model_dump()}


# --------------------------------------------------
# 6. Validate candidate analysis
# --------------------------------------------------

def validate_output_node(
    state: ScreeningState,
) -> dict[str, Any]:

    analysis = state["ai_analysis"]
    score = analysis["match_score"]

    expected_assessment = assessment_from_score(score)

    if analysis["overall_assessment"] != expected_assessment:
        raise ValueError(
            "Screening assessment is inconsistent "
            "with the match score."
        )

    return {}


# --------------------------------------------------
# 7. Build LangGraph workflow
# --------------------------------------------------

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


# --------------------------------------------------
# 8. Execute screening workflow
# --------------------------------------------------

def run_screening_graph(
    job_title: str,
    job_description: str,
    resume_text: str,
    prevalidated_alignment: dict | None = None,
) -> dict[str, Any]:

    initial_state: ScreeningState = {
        "job_title": job_title,
        "job_description": job_description,
        "resume_text": resume_text,
    }

    if prevalidated_alignment is not None:
        initial_state["job_alignment"] = (
            prevalidated_alignment
        )

    return screening_graph.invoke(initial_state)

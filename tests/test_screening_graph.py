
from unittest.mock import patch

import pytest

from app.models.schemas import CandidateAnalysis, JobAlignment
from app.services.screening_graph import (
    build_prompt_node,
    route_after_alignment,
    run_screening_graph,
    validate_output_node,
)


JOB_TITLE = "Python Developer"

JOB_DESCRIPTION = (
    "Develop Python APIs using FastAPI, "
    "SQL, and automated testing."
)

RESUME_TEXT = (
    "Python developer experienced with "
    "FastAPI, SQL, and REST APIs."
)


def make_alignment(status="aligned"):
    return JobAlignment(
        status=status,
        reason=f"Synthetic {status} alignment.",
    )


def make_analysis(score=85, assessment="Strong Match"):
    return CandidateAnalysis(
        match_score=score,
        matching_skills=["Python", "FastAPI"],
        missing_skills=["Docker"],
        candidate_strengths=["API development"],
        experience_alignment="Relevant Python experience.",
        potential_gaps=["Limited Docker evidence"],
        recruiter_questions=[
            "Have you deployed APIs using Docker?"
        ],
        overall_assessment=assessment,
        assessment_reasoning=(
            "The resume demonstrates relevant skills."
        ),
    )


def run_graph(prevalidated_alignment=None):
    return run_screening_graph(
        job_title=JOB_TITLE,
        job_description=JOB_DESCRIPTION,
        resume_text=RESUME_TEXT,
        prevalidated_alignment=prevalidated_alignment,
    )


# --------------------------------------------------
# 1. Successful screening
# --------------------------------------------------

def test_aligned_job_completes_screening():
    with (
        patch(
            "app.services.screening_graph.validate_job_alignment",
            return_value=make_alignment(),
        ),
        patch(
            "app.services.screening_graph.analyze_with_llm",
            return_value=make_analysis(),
        ) as analysis_mock,
    ):
        result = run_graph()

    assert result["job_alignment"]["status"] == "aligned"
    assert result["ai_analysis"]["match_score"] == 85
    assert (
        result["ai_analysis"]["overall_assessment"]
        == "Strong Match"
    )

    analysis_mock.assert_called_once()


# --------------------------------------------------
# 2. Conflict stops screening
# --------------------------------------------------

def test_conflicting_job_stops_screening():
    with (
        patch(
            "app.services.screening_graph.validate_job_alignment",
            return_value=make_alignment("conflict"),
        ),
        patch(
            "app.services.screening_graph.analyze_with_llm",
        ) as analysis_mock,
    ):
        result = run_graph()

    assert result["job_alignment"]["status"] == "conflict"
    assert "ai_analysis" not in result

    analysis_mock.assert_not_called()


# --------------------------------------------------
# 3. Unclear alignment stops screening
# --------------------------------------------------

def test_unclear_job_stops_screening():
    with (
        patch(
            "app.services.screening_graph.validate_job_alignment",
            return_value=make_alignment("unclear"),
        ),
        patch(
            "app.services.screening_graph.analyze_with_llm",
        ) as analysis_mock,
    ):
        result = run_graph()

    assert result["job_alignment"]["status"] == "unclear"
    assert "ai_analysis" not in result

    analysis_mock.assert_not_called()


# --------------------------------------------------
# 4. Prevalidated alignment is reused
# --------------------------------------------------

def test_prevalidated_alignment_skips_llm_validation():
    alignment = make_alignment().model_dump()

    with (
        patch(
            "app.services.screening_graph.validate_job_alignment",
        ) as alignment_mock,
        patch(
            "app.services.screening_graph.analyze_with_llm",
            return_value=make_analysis(),
        ),
    ):
        result = run_graph(
            prevalidated_alignment=alignment
        )

    assert result["job_alignment"] == alignment

    alignment_mock.assert_not_called()


# --------------------------------------------------
# 5. Prompt construction
# --------------------------------------------------

def test_prompt_node_builds_screening_prompt():
    state = {
        "job_title": JOB_TITLE,
        "job_description": JOB_DESCRIPTION,
        "resume_text": RESUME_TEXT,
    }

    with patch(
        "app.services.screening_graph.build_screening_prompt",
        return_value="Synthetic screening prompt",
    ) as prompt_mock:
        result = build_prompt_node(state)

    assert result["screening_prompt"] == (
        "Synthetic screening prompt"
    )

    prompt_mock.assert_called_once_with(
        resume_text=RESUME_TEXT,
        job_description=JOB_DESCRIPTION,
        job_title=JOB_TITLE,
    )


# --------------------------------------------------
# 6. Routing
# --------------------------------------------------

@pytest.mark.parametrize(
    "status, expected_route",
    [
        ("aligned", "continue"),
        ("conflict", "stop"),
        ("unclear", "stop"),
    ],
)
def test_alignment_routing(status, expected_route):
    state = {
        "job_alignment": {
            "status": status,
            "reason": "Synthetic test.",
        }
    }

    assert route_after_alignment(state) == expected_route


# --------------------------------------------------
# 7. Valid score-to-assessment combinations
# --------------------------------------------------

@pytest.mark.parametrize(
    "score, assessment",
    [
        (49, "Weak Match"),
        (50, "Needs Human Review"),
        (69, "Needs Human Review"),
        (70, "Potential Match"),
        (84, "Potential Match"),
        (85, "Strong Match"),
    ],
)
def test_output_validation_accepts_consistent_scores(
    score,
    assessment,
):
    state = {
        "ai_analysis": make_analysis(
            score=score,
            assessment=assessment,
        ).model_dump()
    }

    assert validate_output_node(state) == {}


# --------------------------------------------------
# 8. Inconsistent assessment is rejected
# --------------------------------------------------

def test_output_validation_rejects_inconsistent_score():
    state = {
        "ai_analysis": make_analysis(
            score=35,
            assessment="Strong Match",
        ).model_dump()
    }

    with pytest.raises(
        ValueError,
        match="inconsistent",
    ):
        validate_output_node(state)


# --------------------------------------------------
# 9. Graph rejects inconsistent analysis
# --------------------------------------------------

def test_graph_rejects_inconsistent_analysis():
    alignment = make_alignment().model_dump()

    with patch(
        "app.services.screening_graph.analyze_with_llm",
        return_value=make_analysis(
            score=35,
            assessment="Strong Match",
        ),
    ):
        with pytest.raises(
            ValueError,
            match="inconsistent",
        ):
            run_graph(
                prevalidated_alignment=alignment
            )


# --------------------------------------------------
# 10. AI failure propagates
# --------------------------------------------------

def test_graph_propagates_analysis_failure():
    alignment = make_alignment().model_dump()

    with patch(
        "app.services.screening_graph.analyze_with_llm",
        side_effect=RuntimeError(
            "Synthetic AI service failure"
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Synthetic AI service failure",
        ):
            run_graph(
                prevalidated_alignment=alignment
            )

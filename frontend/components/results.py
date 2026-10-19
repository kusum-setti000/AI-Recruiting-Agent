
"""Candidate screening results component for TalentFlow AI."""

import json
from typing import Any

import streamlit as st


def render_list(
    items: list[str] | None,
    empty_message: str = "Not identified.",
) -> None:
    """Display a list of candidate assessment details."""

    if not items:
        st.caption(empty_message)
        return

    for item in items:
        st.markdown(f"- {item}")


def render_results() -> None:
    """Display the screening result stored in Streamlit session state."""

    result = st.session_state.get("screening_result")

    if not result:
        return

    analysis = result.get("ai_analysis")

    if not isinstance(analysis, dict):
        st.error("Candidate analysis is unavailable.")
        return

    st.divider()
    st.subheader("Candidate Screening Report")

    st.success("Candidate screening completed successfully.")

    candidate_resume = result.get(
        "candidate_resume",
        "Uploaded resume",
    )

    job_title = result.get(
        "job_title",
        "Not specified",
    )

    st.write("**Candidate Resume:**", candidate_resume)
    st.write("**Job Title:**", job_title)

    # -----------------------------------------------------
    # MATCH SCORE AND ASSESSMENT
    # -----------------------------------------------------

    score = analysis.get("match_score", 0)
    assessment = analysis.get(
        "overall_assessment",
        "Needs Human Review",
    )

    score_col, assessment_col = st.columns(2)

    with score_col:
        st.metric(
            "Match Score",
            f"{score}/100",
        )

    with assessment_col:
        st.metric(
            "Overall Assessment",
            assessment,
        )

    if isinstance(score, int) and not isinstance(score, bool):
        st.progress(max(0, min(score, 100)) / 100)

    reasoning = analysis.get("assessment_reasoning")

    if reasoning:
        st.markdown("#### Assessment Reasoning")
        st.write(reasoning)

    # -----------------------------------------------------
    # SKILLS AND STRENGTHS
    # -----------------------------------------------------

    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("#### Matching Skills")
        render_list(
            analysis.get("matching_skills"),
            "No matching skills identified.",
        )

        st.markdown("#### Candidate Strengths")
        render_list(
            analysis.get("candidate_strengths"),
            "No strengths identified.",
        )

    with right_col:
        st.markdown("#### Missing Skills")
        render_list(
            analysis.get("missing_skills"),
            "No missing skills identified.",
        )

        st.markdown("#### Potential Gaps")
        render_list(
            analysis.get("potential_gaps"),
            "No potential gaps identified.",
        )

    # -----------------------------------------------------
    # EXPERIENCE ALIGNMENT
    # -----------------------------------------------------

    st.markdown("#### Experience Alignment")

    experience_alignment = analysis.get(
        "experience_alignment"
    )

    if experience_alignment:
        st.write(experience_alignment)
    else:
        st.caption("No experience alignment details available.")

    # -----------------------------------------------------
    # RECRUITER QUESTIONS
    # -----------------------------------------------------

    st.markdown("#### Suggested Recruiter Questions")

    render_list(
        analysis.get("recruiter_questions"),
        "No recruiter questions generated.",
    )

    # -----------------------------------------------------
    # JOB ALIGNMENT
    # -----------------------------------------------------

    alignment = result.get("job_alignment") or {}

    with st.expander("Job Alignment Details"):
        st.write(
            "**Status:**",
            alignment.get("status", "Unknown"),
        )

        st.write(
            "**Reason:**",
            alignment.get("reason", "Not provided"),
        )

    # -----------------------------------------------------
    # REPORT DOWNLOAD
    # -----------------------------------------------------

    st.divider()

    report_json = json.dumps(
        result,
        indent=2,
        ensure_ascii=False,
    )

    st.download_button(
        label="Download Screening Report (JSON)",
        data=report_json,
        file_name="talentflow_screening_report.json",
        mime="application/json",
        use_container_width=True,
    )

    with st.expander("View Raw Structured Analysis"):
        st.json(result)

    st.caption(
        "This AI-generated assessment is intended to support "
        "recruiter review, not automate hiring decisions."
    )

"""Compact, evidence-preserving executive screening report."""

import html
import json
from typing import Any

import streamlit as st


def _safe(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def _skill_panel(title: str, items: Any, tone: str) -> None:
    values = _items(items)
    chips = "".join(
        f'<span class="tf-chip tf-chip-{tone}">{_safe(item)}</span>'
        for item in values[:12]
    )
    if not chips:
        chips = '<span class="tf-panel-empty">None identified</span>'
    st.html(
        f'<div class="tf-panel tf-skill-panel">'
        f'<div class="tf-panel-title">{_safe(title)} '
        f'<span class="tf-count">{len(values)}</span></div>'
        f'<div class="tf-chips">{chips}</div></div>'
    )
    if len(values) > 12:
        with st.expander(f"Show all {len(values)} — {title}"):
            for item in values:
                st.write("•", item)


def _detail_panel(title: str, items: Any, tone: str) -> None:
    values = _items(items)
    previews = "".join(
        f'<li>{_safe(item)}</li>' for item in values[:3]
    ) or '<li class="tf-panel-empty">None identified</li>'
    st.html(
        f'<div class="tf-panel tf-detail-panel tf-detail-{tone}">'
        f'<div class="tf-panel-title">{_safe(title)} '
        f'<span class="tf-count">{len(values)}</span></div>'
        f'<ul>{previews}</ul></div>'
    )
    if len(values) > 3:
        with st.expander(f"View all {len(values)} — {title}"):
            for item in values:
                st.write("•", item)


def render_results() -> None:
    """Render results from the existing LangGraph session state, without modifying them."""
    result = st.session_state.get("screening_result")
    if not isinstance(result, dict):
        return
    analysis = result.get("ai_analysis")
    if not isinstance(analysis, dict):
        st.error("Candidate analysis is unavailable.")
        return

    st.html("""
    <div class="tf-section-heading tf-results-heading">
      <div><span class="tf-kicker">02 / CANDIDATE INTELLIGENCE</span>
      <h2>Executive assessment</h2>
      <p>A structured view of the model's evidence and recommendations.</p></div>
      <span class="tf-complete">● Analysis complete</span>
    </div>
    """)

    raw_score = analysis.get("match_score")
    score = raw_score if isinstance(raw_score, (int, float)) and not isinstance(raw_score, bool) and 0 <= raw_score <= 100 else None
    assessment = analysis.get("overall_assessment") or "Needs Human Review"
    reasoning = analysis.get("assessment_reasoning") or "No assessment reasoning provided."
    job_title = result.get("job_title") or "Not specified"
    resume = result.get("candidate_resume") or "Uploaded resume"

    score_label = f"{score:g}%" if score is not None else "N/A"
    progress = f"{score:g}%" if score is not None else "0%"
    st.html(
        f'<section class="tf-summary">'
        f'<div class="tf-score-ring" style="--score:{progress}">'
        f'<div class="tf-score-core"><strong>{_safe(score_label)}</strong>'
        f'<small>Match score</small></div></div>'
        f'<div class="tf-summary-copy">'
        f'<span class="tf-kicker">CANDIDATE OVERVIEW</span>'
        f'<h3>{_safe(assessment)}</h3>'
        f'<p class="tf-summary-meta"><b>Role:</b> {_safe(job_title)}</p>'
        f'<p class="tf-summary-meta"><b>Resume:</b> {_safe(resume)}</p>'
        f'<p class="tf-summary-reason">{_safe(reasoning)}</p>'
               f'</div></section>'
    )

    # Skill analysis
    st.html(
        '<div class="tf-section-heading">'
        '<div><span class="tf-kicker">SKILL ANALYSIS</span>'
        '<h2>Skills alignment</h2>'
        '<p>Skills identified from the resume and job requirements.</p>'
        '</div></div>'
    )

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        _skill_panel(
            "Matching skills",
            analysis.get("matching_skills", []),
            "match",
        )

    with col2:
        _skill_panel(
            "Missing skills",
            analysis.get("missing_skills", []),
            "missing",
        )

    # Candidate evaluation
    st.html(
        '<div class="tf-section-heading">'
        '<div><span class="tf-kicker">CANDIDATE EVALUATION</span>'
        '<h2>Strengths and gaps</h2>'
        '</div></div>'
    )

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        _detail_panel(
            "Candidate strengths",
            analysis.get("candidate_strengths", []),
            "positive",
        )

    with col2:
        _detail_panel(
            "Areas for improvement",
            analysis.get("potential_gaps", []),
            "warning",
        )

    # Recruiter interview questions
    st.html(
        '<div class="tf-section-heading">'
        '<div><span class="tf-kicker">RECRUITER INSIGHTS</span>'
        '<h2>Suggested interview questions</h2>'
        '</div></div>'
    )

    questions = _items(
        analysis.get("recruiter_questions", [])
    )

    if questions:
        for index, question in enumerate(questions, start=1):
            st.markdown(f"**Q{index}.** {question}")
    else:
        st.info("No interview questions were generated.")

    # Detailed analysis
    with st.expander("View complete AI assessment"):
        st.json(analysis)

    # Download screening result
    st.download_button(
        label="Download assessment JSON",
        data=json.dumps(result, indent=2, default=str),
        file_name="talentflow_assessment.json",
        mime="application/json",
        key="download_assessment_json",
    )

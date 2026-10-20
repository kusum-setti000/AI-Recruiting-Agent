"""TalentFlow AI — executive screening dashboard."""

import logging
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.components.sidebar import render_sidebar
from frontend.components.screening_form import render_screening_form
from frontend.components.results import render_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="TalentFlow AI | Executive Dashboard",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css() -> None:
    css_path = Path(__file__).resolve().parent / "styles" / "main.css"
    if css_path.is_file():
        st.html(f"<style>{css_path.read_text(encoding='utf-8')}</style>")
    else:
        logger.warning("Stylesheet not found: %s", css_path)


def main() -> None:
    load_css()
    render_sidebar()

    st.html("""
    <section class="tf-hero">
      <div class="tf-kicker">RECRUITMENT REIMAGINED · TALENTFLOW AI</div>
      <h1>Find exceptional talent <span>with AI.</span></h1>
      <p>Turn resumes and job requirements into structured, evidence-based
      candidate assessments. Built for thoughtful human decisions.</p>
      <div class="tf-hero-tags"><span>✦ Evidence-based scoring</span>
      <span>◇ Skill gap analysis</span><span>↗ Recruiter insights</span></div>
    </section>
    """)

    st.html("""
    <div class="tf-section-heading">
      <div><span class="tf-kicker">01 / SCREENING</span>
      <h2>Screen a candidate</h2>
      <p>Provide a job description and upload a PDF or DOCX resume.</p></div>
    </div>
    """)
    with st.container(border=True):
        render_screening_form()

    if st.session_state.get("screening_result"):
        render_results()
    else:
        st.html("""
        <div class="tf-empty">
          <div class="tf-empty-symbol">✦</div>
          <div><strong>Assessment workspace</strong>
          <p>Your executive summary, score, skills, gaps and interview
          questions will appear here when screening completes.</p></div>
        </div>
        """)

    st.caption("TalentFlow AI · Streamlit + LangGraph + OpenAI · Human review required")


if __name__ == "__main__":
    main()


"""TalentFlow AI — Streamlit application entry point."""

import logging
import sys
from pathlib import Path

import streamlit as st


# ---------------------------------------------------------
# PROJECT IMPORT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from frontend.components.sidebar import render_sidebar
from frontend.components.screening_form import (
    render_screening_form,
)
from frontend.components.results import render_results


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="TalentFlow AI | Recruiting Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# CSS
# ---------------------------------------------------------

def load_css() -> None:
    """Load the frontend stylesheet."""

    css_path = (
        Path(__file__).resolve().parent
        / "styles"
        / "main.css"
    )

    if not css_path.is_file():
        logger.warning(
            "Frontend stylesheet not found: %s",
            css_path,
        )
        return

    css = css_path.read_text(encoding="utf-8")

    st.html(f"<style>{css}</style>")


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

def main() -> None:
    """Render the TalentFlow recruiting interface."""

    load_css()

    # Sidebar
    render_sidebar()

    # Header
    st.markdown(
        """
        <div class="hero">
            <h1>TalentFlow AI</h1>
            <p>
                Intelligent candidate screening powered by
                LangChain and LangGraph.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        "Upload a candidate resume and provide the job "
        "requirements to generate an AI-assisted screening report."
    )

    # Screening form and LangGraph execution
    render_screening_form()

    # Candidate assessment and report download
    render_results()

    st.divider()

    st.caption(
        "TalentFlow AI | Streamlit + LangChain + LangGraph | "
        "Human-in-the-loop recruiting"
    )


if __name__ == "__main__":
    main()

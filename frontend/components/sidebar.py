
"""Sidebar component for the TalentFlow AI frontend."""

import logging

import streamlit as st

from app.agents.graph import create_screening_graph


logger = logging.getLogger(__name__)


def render_sidebar() -> None:
    """Render the sidebar and check LangGraph readiness."""

    with st.sidebar:
        st.markdown("## 🎯 TalentFlow AI")

        st.caption(
            "AI-powered candidate screening using "
            "LangChain, LangGraph, and OpenAI."
        )

        st.divider()

        st.markdown("### Agent Status")

        if st.button(
            "Check Agent Status",
            key="sidebar_agent_status",
            use_container_width=True,
        ):
            try:
                graph = create_screening_graph()
                graph.get_graph()

            except Exception:
                logger.exception(
                    "Failed to initialize the screening graph."
                )

                st.error(
                    "LangGraph workflow initialization failed."
                )

            else:
                st.success(
                    "LangGraph workflow is ready."
                )

        st.caption(
            "This checks graph initialization, "
            "not OpenAI API connectivity."
        )

        st.divider()

        st.markdown("### Screening Workflow")

        st.markdown(
            """
            1. Validate job alignment
            2. Extract resume content
            3. Analyze candidate
            4. Validate assessment
            5. Review screening results
            """
        )

        st.divider()

        st.markdown("### Technology Stack")

        st.caption(
            "Frontend: Streamlit"
        )
        st.caption(
            "Orchestration: LangGraph"
        )
        st.caption(
            "LLM Integration: LangChain + OpenAI"
        )

        st.divider()

        st.info(
            "AI-generated assessments are decision-support "
            "tools. All hiring decisions require human review."
        )

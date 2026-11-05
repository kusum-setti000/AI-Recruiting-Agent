
"""Candidate screening form for TalentFlow AI."""

import logging

import streamlit as st

from app.agents.document_loader import (
    ResumeValidationError,
    validate_resume_upload,
)
from app.agents.graph import run_screening_graph


logger = logging.getLogger(__name__)


def initialize_screening_state() -> None:
    """Initialize persistent Streamlit session values."""

    if "screening_result" not in st.session_state:
        st.session_state.screening_result = None

    if "screening_error" not in st.session_state:
        st.session_state.screening_error = None


def render_screening_form() -> None:
    """Render the form and execute the LangGraph workflow."""

    initialize_screening_state()

    st.markdown("### New Candidate Screening")

    with st.form("candidate_screening_form"):
        job_title = st.text_input(
            "Job Title",
            placeholder="e.g. Senior AI/ML Engineer",
        )

        job_description = st.text_area(
            "Job Description",
            placeholder=(
                "Enter the responsibilities, required skills, "
                "experience, and qualifications."
            ),
            height=230,
        )

        uploaded_file = st.file_uploader(
            "Candidate Resume",
            type=["pdf", "docx"],
            help="PDF or DOCX, maximum 5 MB.",
        )

        submitted = st.form_submit_button(
            "Analyze Candidate",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        st.session_state.screening_result = None
        st.session_state.screening_error = None

        if not job_title.strip():
            st.session_state.screening_error = (
                "Please enter a job title."
            )

        elif not job_description.strip():
            st.session_state.screening_error = (
                "Please enter a job description."
            )

        elif uploaded_file is None:
            st.session_state.screening_error = (
                "Please upload a candidate resume."
            )

        else:
            try:
                resume_bytes = uploaded_file.getvalue()

                # Reject invalid uploads before model invocation.
                validate_resume_upload(
                    filename=uploaded_file.name,
                    file_bytes=resume_bytes,
                )

                with st.spinner(
                    "Validating job alignment and screening candidate..."
                ):
                    result = run_screening_graph(
                        job_title=job_title.strip(),
                        job_description=job_description.strip(),
                        resume_filename=uploaded_file.name,
                        resume_bytes=resume_bytes,
                    )

                alignment = result.get("job_alignment") or {}
                analysis = result.get("ai_analysis")

                if alignment.get("status") != "aligned":
                    st.session_state.screening_error = (
                        "Job alignment requires review: "
                        + str(
                            alignment.get(
                                "reason",
                                "The role requirements are unclear.",
                            )
                        )
                    )

                elif not isinstance(analysis, dict):
                    st.session_state.screening_error = (
                        "The screening agent returned no "
                        "candidate analysis."
                    )

                else:
                    st.session_state.screening_result = result

            except ResumeValidationError as exc:
                st.session_state.screening_error = str(exc)

            except Exception:
                logger.exception("Candidate screening failed")

                st.session_state.screening_error = (
                    "Candidate screening failed. "
                    "Check the application logs and model configuration."
                )

    if st.session_state.screening_error:
        st.error(st.session_state.screening_error)

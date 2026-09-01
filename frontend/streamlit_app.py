import streamlit as st
import requests


st.set_page_config(
    page_title="AI Recruiting Agent",
    page_icon="🤖",
    layout="wide"
)


st.title("AI Recruiting Agent")
st.caption(
    "Upload a candidate resume and compare it against a job description."
)


left_col, right_col = st.columns([1, 1])

with left_col:
    job_title = st.text_input("Job Title")

with right_col:
    uploaded_file = st.file_uploader(
        "Upload Resume",
        type=["pdf", "docx"]
    )


job_description = st.text_area(
    "Job Description",
    height=180
)


analyze_button = st.button(
    "Analyze Candidate",
    type="primary",
    use_container_width=True
)


if analyze_button:

    if not job_title:
        st.warning("Please enter a job title.")

    elif not job_description:
        st.warning("Please enter a job description.")

    elif uploaded_file is None:
        st.warning("Please upload a resume.")

    else:

        with st.spinner("Analyzing candidate..."):

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }

            data = {
                "job_title": job_title,
                "job_description": job_description
            }

            try:

                response = requests.post(
                    "http://127.0.0.1:8000/analyze-candidate",
                    files=files,
                    data=data
                )

                if response.status_code == 200:

                    result = response.json()
                    analysis = result["ai_analysis"]

                    st.success("Candidate analysis completed.")

                    st.divider()

                    # -----------------------------------------
                    # CANDIDATE SUMMARY
                    # -----------------------------------------

                    st.subheader("Candidate Summary")

                    summary_col1, summary_col2, summary_col3 = st.columns(3)

                    with summary_col1:
                        st.metric(
                            "Candidate Resume",
                            result["candidate_resume"]
                        )

                    with summary_col2:
                        st.metric(
                            "Match Score",
                            f"{analysis['match_score']}%"
                        )

                    with summary_col3:
                        st.metric(
                            "Overall Assessment",
                            analysis["overall_assessment"]
                        )

                    st.divider()

                    # -----------------------------------------
                    # SKILLS
                    # -----------------------------------------

                    skills_col1, skills_col2 = st.columns(2)

                    with skills_col1:

                        st.subheader("Matching Skills")

                        for skill in analysis["matching_skills"]:
                            st.success(skill)

                    with skills_col2:

                        st.subheader("Missing / Unverified Skills")

                        for skill in analysis["missing_skills"]:
                            st.warning(skill)

                    st.divider()

                    # -----------------------------------------
                    # STRENGTHS
                    # -----------------------------------------

                    st.subheader("Candidate Strengths")

                    for strength in analysis["candidate_strengths"]:
                        st.write(f"• {strength}")

                    st.divider()

                    # -----------------------------------------
                    # EXPERIENCE ALIGNMENT
                    # -----------------------------------------

                    st.subheader("Experience Alignment")

                    st.info(
                        analysis["experience_alignment"]
                    )

                    st.divider()

                    # -----------------------------------------
                    # POTENTIAL GAPS
                    # -----------------------------------------

                    st.subheader("Potential Gaps")

                    for gap in analysis["potential_gaps"]:
                        st.write(f"• {gap}")

                    st.divider()

                    # -----------------------------------------
                    # RECRUITER QUESTIONS
                    # -----------------------------------------

                    st.subheader("Recruiter Questions")

                    for number, question in enumerate(
                        analysis["recruiter_questions"],
                        start=1
                    ):
                        st.write(
                            f"**{number}.** {question}"
                        )

                    st.divider()

                    # -----------------------------------------
                    # ASSESSMENT REASONING
                    # -----------------------------------------

                    st.subheader("Assessment Reasoning")

                    st.write(
                        analysis["assessment_reasoning"]
                    )

                else:

                    st.error(
                        f"Backend error: {response.text}"
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Could not connect to the FastAPI backend. "
                    "Make sure Uvicorn is running."
                )
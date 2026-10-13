import requests
import streamlit as st


st.set_page_config(
    page_title="AI Recruiting Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("AI Recruiting Agent")
st.caption(
    "Check the job title and description, "
    "then compare a candidate's resume against the role."
)

BACKEND_URL = "http://127.0.0.1:8002/analyze-candidate"
st.write("Backend URL in use:", BACKEND_URL)

left_col, right_col = st.columns(2)

with left_col:
    job_title = st.text_input("Job Title")

with right_col:
    uploaded_file = st.file_uploader(
        "Upload Resume",
        type=["pdf", "docx"],
    )

job_description = st.text_area(
    "Job Description",
    height=180,
)

analyze_button = st.button(
    "Analyze Candidate",
    type="primary",
    use_container_width=True,
)


if analyze_button:
    cleaned_title = job_title.strip()
    cleaned_description = job_description.strip()

    if not cleaned_title:
        st.warning("Please enter a job title.")

    elif not cleaned_description:
        st.warning("Please enter a job description.")

    elif uploaded_file is None:
        st.warning("Please upload a resume.")

    else:
        with st.spinner(
            "Checking the role and analyzing the candidate..."
        ):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            }

            data = {
                "job_title": cleaned_title,
                "job_description": cleaned_description,
            }

            try:
                response = requests.post(
                    BACKEND_URL,
                    files=files,
                    data=data,
                    timeout=180,
                )

                if response.status_code == 200:
                    result = response.json()

                    # Temporary diagnostic output.
                    st.write(
                        "Backend response keys:",
                        list(result.keys()),
                    )

                    if "job_alignment" not in result:
                        st.error(
                            "The backend response is missing "
                            "'job_alignment'. The running backend "
                            "does not match the updated API response."
                        )

                        st.info(
                            "Save app/main.py, stop FastAPI with "
                            "Ctrl+C, and restart it on port 8001. "
                            "Copy the response keys shown above "
                            "to help diagnose the issue."
                        )

                        st.stop()

                    analysis = result["ai_analysis"]
                    alignment = result["job_alignment"]

                    if alignment.get("status") != "aligned":
                        st.warning(
                            "The job title and description "
                            "need correction or clarification."
                        )

                        st.write(
                            alignment.get(
                                "reason",
                                "Please check the role information.",
                            )
                        )

                        st.stop()

                    st.success("Candidate analysis completed.")

                    st.subheader("Job Title and Description Check")
                    st.write(
                        f"**Job title:** {result['job_title']}"
                    )
                    st.info(alignment["reason"])

                    st.divider()
                    st.subheader("Candidate Summary")

                    st.write(
                        f"**Resume:** {result['candidate_resume']}"
                    )

                    score_col, assessment_col = st.columns(2)

                    with score_col:
                        st.metric(
                            "Estimated Match Score",
                            f"{analysis['match_score']}%",
                        )

                    with assessment_col:
                        st.metric(
                            "Overall Assessment",
                            analysis["overall_assessment"],
                        )

                    st.caption(
                        "The score is an AI estimate of resume alignment, "
                        "not a probability of job success."
                    )

                    st.divider()

                    matching_col, missing_col = st.columns(2)

                    with matching_col:
                        st.subheader("Matching Skills")

                        if analysis["matching_skills"]:
                            for skill in analysis["matching_skills"]:
                                st.success(skill)
                        else:
                            st.write(
                                "No supported matches identified."
                            )

                    with missing_col:
                        st.subheader("Missing / Unverified Skills")

                        if analysis["missing_skills"]:
                            for skill in analysis["missing_skills"]:
                                st.warning(skill)
                        else:
                            st.write(
                                "No missing requirements identified."
                            )

                    st.divider()
                    st.subheader("Candidate Strengths")

                    for strength in analysis["candidate_strengths"]:
                        st.write(f"• {strength}")

                    st.divider()
                    st.subheader("Experience Alignment")
                    st.info(analysis["experience_alignment"])

                    st.divider()
                    st.subheader("Potential Gaps")

                    for gap in analysis["potential_gaps"]:
                        st.write(f"• {gap}")

                    st.divider()
                    st.subheader("Recruiter Questions")

                    for number, question in enumerate(
                        analysis["recruiter_questions"],
                        start=1,
                    ):
                        st.write(f"**{number}.** {question}")

                    st.divider()
                    st.subheader("Assessment Reasoning")
                    st.write(analysis["assessment_reasoning"])

                    st.divider()
                    st.caption(
                        "AI-generated recruiting support. "
                        "Final hiring decisions require human review."
                    )

                elif response.status_code == 422:
                    detail = response.json().get(
                        "detail",
                        "Please check your inputs.",
                    )

                    if isinstance(detail, dict):
                        status = detail.get("status")

                        if status == "conflict":
                            st.error(
                                "Job title and description conflict."
                            )
                        else:
                            st.warning(
                                "Job title and description "
                                "need clarification."
                            )

                        st.write(
                            detail.get(
                                "message",
                                "Please check the role information.",
                            )
                        )

                        st.info(
                            "Correct or clarify the title and description, "
                            "then try again. No match score was generated."
                        )

                    elif isinstance(detail, str):
                        st.warning(detail)

                    else:
                        st.warning(
                            "Please provide a valid job title, "
                            "job description, and resume."
                        )

                else:
                    try:
                        detail = response.json().get(
                            "detail",
                            response.text,
                        )
                    except ValueError:
                        detail = response.text

                    st.error(
                        f"Backend error ({response.status_code}): "
                        f"{detail}"
                    )

            except requests.exceptions.Timeout:
                st.error(
                    "The analysis took too long. "
                    "Check the backend terminal and try again."
                )

            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to FastAPI. "
                    "Make sure the backend is running on port 8001."
                )

            except requests.exceptions.RequestException as error:
                st.error(f"Request failed: {error}")

            except Exception as error:
                st.error(f"Unexpected error: {error}")
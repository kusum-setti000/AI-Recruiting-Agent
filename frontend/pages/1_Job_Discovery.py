import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from app.integrations.job_discovery.models import CandidateJobProfile
from app.integrations.job_discovery.service import JobDiscoveryService
from app.integrations.job_discovery.resume_profiler import profile_from_resume
from app.integrations.job_discovery.linkedin_search import linkedin_search_urls

st.set_page_config(page_title="Job Discovery", layout="wide")
st.title("AI Job Discovery")
st.caption("Resume-based job recommendations")

with st.form("discovery"):
    resume = st.file_uploader("Resume", type=["pdf", "docx"])
    location = st.text_input("Location", "United States")
    remote = st.checkbox("Remote only")
    submit = st.form_submit_button("Discover Jobs", type="primary")

if submit:
    if resume is None:
        st.error("Upload a resume first.")
    else:
        try:
            with st.spinner("Analyzing resume and finding jobs..."):
                profile = profile_from_resume(
                    resume.name, resume.getvalue(),
                    location=location.strip() or None,
                    remote_only=remote,
                )
                result = JobDiscoveryService().search(profile)
            st.session_state["job_profile"] = profile
            st.session_state["job_results"] = result.jobs
        except Exception as exc:
            st.error(f"Discovery failed: {type(exc).__name__}")
            st.info("Check the Streamlit terminal for details.")
            import traceback
            traceback.print_exc()

profile = st.session_state.get("job_profile")
jobs = st.session_state.get("job_results")

if profile is not None:
    st.subheader("Candidate profile")
    st.json(profile.model_dump())

    st.subheader("LinkedIn searches")
    for title, url in linkedin_search_urls(profile):
        st.link_button(title, url)

if jobs is not None:
    st.metric("Jobs found", len(jobs))
    keyword = st.text_input("Search results")
    threshold = st.slider("Minimum match score", 0, 100, 0)

    filtered = [
        job for job in jobs
        if (job.match_score or 0) >= threshold
        and keyword.lower() in (
            job.title + " " + job.company + " " + (job.location or "")
        ).lower()
    ]

    for job in filtered:
        with st.container(border=True):
            st.subheader(job.title)
            st.write(f"{job.company} | {job.location or 'Location unspecified'}")
            st.metric("Match", f"{job.match_score or 0}%")
            if job.recommendation_summary:
                st.write(job.recommendation_summary)
            if job.match_explanation:
                with st.expander("Match explanation"):
                    st.json(job.match_explanation.model_dump())
            st.link_button("View job / Apply", str(job.job_url))


import json

st.divider()
st.header("Saved Job Recommendations")

snapshot_path = ROOT / "data/job_discovery_snapshot.json"

if snapshot_path.exists():
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    saved_jobs = snapshot.get("jobs", [])

    st.success(f"{len(saved_jobs)} jobs available from automated discovery")
    st.caption(f"Last updated: {snapshot.get('checked_at', 'Unknown')}")

    search_saved = st.text_input("Filter saved jobs", key="saved_search")
    minimum_score = st.slider(
        "Minimum saved-job match score", 0, 100, 0,
        key="saved_min_score"
    )

    matches = [
        job for job in saved_jobs
        if (job.get("match_score") or 0) >= minimum_score
        and search_saved.lower() in " ".join(
            str(job.get(field) or "")
            for field in ("title", "company", "location")
        ).lower()
    ]

    st.write(f"Showing {len(matches)} matching jobs")

    for job in matches[:30]:
        with st.container(border=True):
            st.subheader(job.get("title", "Untitled"))
            st.write(
                f"**{job.get('company', 'Unknown')}** | "
                f"{job.get('location', 'Not specified')}"
            )
            st.metric("Match score", f"{job.get('match_score', 0)}%")
            if job.get("recommendation_summary"):
                st.write(job["recommendation_summary"])
            url = str(job.get("job_url") or "")
            if url.startswith(("https://", "http://")):
                st.link_button("View job / Apply", url)
else:
    st.info("No saved discovery results yet. Run the scheduler first.")

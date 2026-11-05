import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.integrations.job_discovery.service import JobDiscoveryService
from app.integrations.job_discovery.resume_profiler import profile_from_resume

st.set_page_config(
    page_title="TalentFlow AI | Browse Jobs",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp {
    background: #0d1117;
    color: #e6eaf0;
}
.block-container {
    max-width: 1800px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}
[data-testid="stHeader"] {
    background: #0d1117;
}
[data-testid="stSidebar"] {
    background: #151a22;
}
h1, h2, h3 {
    letter-spacing: -0.035em;
}
h1 {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
}
h3 {
    font-size: 1.15rem !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #171c24;
    border-color: #303744 !important;
    border-radius: 12px;
}
[data-testid="stMetric"] {
    background: #171c24;
    border: 1px solid #303744;
    border-radius: 10px;
    padding: 12px;
}
.stButton button {
    border-radius: 8px;
    font-weight: 600;
}
.stButton button[kind="primary"],
.stFormSubmitButton button[kind="primary"] {
    background: #e9f0fa;
    color: #10151d;
    border: none;
}
.stButton button[kind="primary"]:hover,
.stFormSubmitButton button[kind="primary"]:hover {
    background: #c7d9f5;
    color: #10151d;
}
.stTextInput input,
[data-baseweb="select"] > div {
    background: #171c24 !important;
    border-color: #303744 !important;
    border-radius: 8px !important;
}
[data-testid="stCaptionContainer"] {
    color: #9ca5b3;
}
div[data-testid="stLinkButton"] a {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


def source_label(job):
    source = job.source.lower()
    if "linkedin" in source or "theirstack" in source:
        return "LinkedIn-sourced · TheirStack"
    if source == "greenhouse":
        return "Greenhouse"
    if source == "ashby":
        return "Ashby"
    if source == "lever":
        return "Lever"
    return job.source.title()


def job_identity(job):
    return (
        job.source,
        job.company,
        str(job.external_id),
        str(job.job_url),
    )


def age_label(job):
    posted = getattr(job, "posted_at", None)
    if not posted:
        return None
    try:
        if isinstance(posted, str):
            posted = datetime.fromisoformat(
                posted.replace("Z", "+00:00")
            )
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        days = max(
            0,
            (datetime.now(timezone.utc) - posted).days,
        )
        return "Today" if days == 0 else f"{days}d ago"
    except (ValueError, TypeError, AttributeError):
        return None


header_left, header_right = st.columns([3, 2])

with header_left:
    st.markdown("# ✦ TALENTFLOW AI")
    st.caption("Direct job discovery · Resume intelligence")

with header_right:
    st.write("")
    st.caption(
        "BROWSE JOBS  ·  MULTI-SOURCE  ·  AI MATCHING"
    )

st.divider()

with st.expander(
    "✦ Upload resume & discover personalized jobs",
    expanded=not bool(st.session_state.get("job_results")),
):
    with st.form("discovery_form"):
        a, b = st.columns([2, 1])

        with a:
            resume = st.file_uploader(
                "Resume (PDF or DOCX)",
                type=["pdf", "docx"],
            )

        with b:
            location = st.text_input(
                "Preferred location",
                value="United States",
            )

        remote_only = st.checkbox("Remote jobs only")

        include_linkedin = st.checkbox(
            "Include LinkedIn-sourced jobs via TheirStack",
            value=False,
            help="Uses TheirStack API credits. Limit: 5 jobs per search.",
        )

        submitted = st.form_submit_button(
            "Find matching jobs",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if resume is None:
            st.warning("Please upload a resume.")
        else:
            try:
                with st.spinner(
                    "Reading resume and discovering opportunities..."
                ):
                    profile = profile_from_resume(
                        resume.name,
                        resume.getvalue(),
                        location=location.strip() or None,
                        remote_only=remote_only,
                    )

                    result = JobDiscoveryService(
                        include_linkedin=include_linkedin
                    ).search(profile)

                st.session_state["job_profile"] = profile
                st.session_state["job_results"] = result.jobs
                st.session_state.pop("selected_job_id", None)

                st.success(
                    f"Found {len(result.jobs)} job opportunities."
                )

            except Exception as exc:
                st.error(
                    f"Discovery failed: {type(exc).__name__}: {exc}"
                )

jobs = st.session_state.get("job_results") or []
profile = st.session_state.get("job_profile")

if not jobs:
    st.info(
        "Upload your resume above to discover jobs from "
        "your configured providers."
    )
    st.stop()

sources = sorted(set(source_label(job) for job in jobs))

st.caption(
    f"{len(jobs):,} discovered jobs · "
    f"{len(set(j.company for j in jobs)):,} companies · "
    f"{len(sources)} sources"
)

search_col, country_col = st.columns([4, 1])

with search_col:
    search_text = st.text_input(
        "Search",
        placeholder=(
            "Search by job title, company, location or skills "
            "(all words must match)"
        ),
        label_visibility="collapsed",
    )

with country_col:
    country = st.selectbox(
        "Country / location",
        ["All locations", "United States", "Remote"],
        label_visibility="collapsed",
    )

filter_columns = st.columns([1.3, 1.3, 1.3, 1.3, 1.3, 1.4])

with filter_columns[0]:
    source_filter = st.selectbox(
        "Source", ["All sources"] + sources
    )

with filter_columns[1]:
    workplace = st.selectbox(
        "Workplace",
        ["All", "Remote", "Hybrid", "On-site"],
    )

with filter_columns[2]:
    minimum_match = st.selectbox(
        "Match score",
        [80, 90, 100],
        index=0,
        format_func=lambda x: f"{x}%+",
    )

with filter_columns[3]:
    sort_order = st.selectbox(
        "Sort",
        ["Best match", "Company A-Z", "Title A-Z"],
    )

with filter_columns[4]:
    title_filter = st.selectbox(
        "Role",
        ["All roles", "Target roles only"],
    )

with filter_columns[5]:
    description_only = st.checkbox(
        "Full JD available",
        value=False,
    )


def matches_job(job):
    if (job.match_score or 0) < minimum_match:
        return False

    if (
        source_filter != "All sources"
        and source_label(job) != source_filter
    ):
        return False

    loc = (job.location or "").lower()

    if workplace != "All":
        terms = {
            "Remote": ["remote", "anywhere", "work from home"],
            "Hybrid": ["hybrid"],
            "On-site": ["on-site", "onsite", "on site"],
        }[workplace]

        if not any(term in loc for term in terms):
            return False

    if country == "Remote" and not any(
        term in loc for term in ["remote", "anywhere"]
    ):
        return False

    if country == "United States":
        # This is a display-only heuristic, not a verified
        # country classification.
        us_tokens = [
            "united states", "usa", "u.s.", ", us",
            ", ca", ", ny", ", tx", ", wa", ", ma",
            ", il", ", co", ", fl", ", ga", ", nj",
            ", va", ", nc", ", az", ", or",
        ]
        if not any(token in loc for token in us_tokens):
            return False

    if description_only and not job.description:
        return False

    if title_filter == "Target roles only" and profile:
        from app.integrations.job_discovery.matcher import (
            title_similarity,
        )
        if not any(
            title_similarity(target, job.title) >= 0.5
            for target in profile.target_titles
        ):
            return False

    searchable = " ".join([
        job.title,
        job.company,
        job.location or "",
        job.description or "",
    ]).lower()

    return all(
        word in searchable
        for word in search_text.lower().split()
    )


filtered = [job for job in jobs if matches_job(job)]

if sort_order == "Best match":
    filtered.sort(
        key=lambda job: job.match_score or 0,
        reverse=True,
    )
elif sort_order == "Company A-Z":
    filtered.sort(key=lambda job: job.company.lower())
else:
    filtered.sort(key=lambda job: job.title.lower())

st.markdown(
    f"**All jobs · {len(filtered):,} results**"
)

left, right = st.columns([0.85, 1.45], gap="medium")

with left:
    st.caption("JOB LISTINGS")

    if not filtered:
        st.info("No jobs match the selected filters.")

    # Limit visible cards to keep Streamlit responsive.
    page_size = 25
    pages = max(1, (len(filtered) + page_size - 1) // page_size)

    page_number = st.number_input(
        "Page",
        min_value=1,
        max_value=pages,
        value=1,
        step=1,
    )

    start = (page_number - 1) * page_size
    visible_jobs = filtered[start:start + page_size]

    for index, job in enumerate(visible_jobs):
        identity = job_identity(job)
        selected = (
            st.session_state.get("selected_job_id")
            == identity
        )

        with st.container(border=True):
            title_col, score_col = st.columns([4, 1])

            with title_col:
                st.markdown(f"**{job.title}**")
                st.write(job.company)

            with score_col:
                st.markdown(
                    f"**{job.match_score or 0}%**"
                )

            st.caption(
                job.location or "Location not specified"
            )

            age = age_label(job)
            label = source_label(job)
            if age:
                label += f" · {age}"
            st.caption(label)

            if st.button(
                "✓ Selected" if selected else "View details",
                key=f"job_{start + index}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state["selected_job_id"] = identity
                st.rerun()

with right:
    st.caption("JOB DETAILS")

    selected_id = st.session_state.get("selected_job_id")

    selected_job = next(
        (
            job for job in filtered
            if job_identity(job) == selected_id
        ),
        filtered[0] if filtered else None,
    )

    if selected_job:
        with st.container(border=True):
            st.caption(source_label(selected_job))

            st.markdown(f"## {selected_job.title}")
            st.markdown(f"**{selected_job.company}**")

            st.caption(
                selected_job.location
                or "Location not specified"
            )

            metric_col, source_col = st.columns(2)

            with metric_col:
                st.metric(
                    "Resume match",
                    f"{selected_job.match_score or 0}%",
                )

            with source_col:
                st.metric(
                    "Source",
                    "TheirStack"
                    if "theirstack" in selected_job.source
                    else selected_job.source.title(),
                )

            st.link_button(
                "Apply Direct / View Original Posting ↗",
                str(selected_job.job_url),
                use_container_width=True,
                type="primary",
            )

            if selected_job.match_explanation:
                matched = (
                    selected_job.match_explanation.matched_skills
                )
                if matched:
                    st.markdown("#### Matched skills")
                    st.write(" · ".join(matched[:20]))

            st.divider()

            st.markdown("### Role Overview")

            if selected_job.description:
                # Render job text as plain Markdown, not unsafe HTML.
                st.markdown(selected_job.description)
            else:
                st.info(
                    "Full description unavailable. "
                    "Open the original job posting."
                )

            if selected_job.recommendation_summary:
                st.divider()
                with st.expander(
                    "✦ Why this job matches your resume"
                ):
                    st.write(
                        selected_job.recommendation_summary
                    )

            if selected_job.match_explanation:
                with st.expander("Detailed match analysis"):
                    st.json(
                        selected_job.match_explanation.model_dump()
                    )

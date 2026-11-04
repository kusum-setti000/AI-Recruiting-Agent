"""TalentFlow AI: browse-first dark job board with optional resume matching."""
import hashlib
import html
import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import streamlit as st
from app.integrations.job_discovery.greenhouse import GreenhouseProvider
from app.integrations.job_discovery.models import CandidateJobProfile, DiscoveredJob
from app.integrations.job_discovery.matcher import calculate_match_score
from app.integrations.job_discovery.resume_profiler import profile_from_resume
from app.integrations.job_discovery.theirstack_provider import TheirStackProvider
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="TalentFlow AI | Jobs", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

BOARDS = ["greenhouse", "datadog", "cloudflare", "figma", "databricks", "mongodb", "elastic", "stripe", "reddit"]
STOP = {"engineer", "engineering", "senior", "junior", "staff", "lead", "principal", "associate", "specialist", "developer", "manager", "the", "and", "of", "for", "in", "ii", "iii"}

st.markdown('\n<style>\n[data-testid="stSidebar"],\n[data-testid="stSidebarNav"],\n[data-testid="collapsedControl"],\n[data-testid="stSidebarCollapsedControl"] {\n    display: none !important;\n}\n[data-testid="stAppViewContainer"] > .main {\n    width: 100% !important;\n}\n.block-container {\n    max-width: 1600px !important;\n    padding-top: 2rem !important;\n}\n</style>\n', unsafe_allow_html=True)

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');
html, body, [class*="css"], .stApp {font-family:'DM Sans',sans-serif!important;}
.stApp {background:#0d1117;color:#e8edf5;}
header[data-testid="stHeader"] {background:#0d1117!important;}
.block-container {max-width:1560px;padding-top:1.15rem;padding-bottom:3rem;}
#MainMenu,footer {visibility:hidden;}
.tf-top {display:flex;align-items:center;justify-content:space-between;padding:7px 0 22px;border-bottom:1px solid #252c36;margin-bottom:18px;}
.tf-brand {font-family:'Space Mono',monospace;letter-spacing:4px;font-weight:700;font-size:20px;color:#f4f6fa;}
.tf-brand span {background:#102d27;color:#63f5b3;border-radius:7px;padding:7px 10px;letter-spacing:0;margin-right:10px;}
.tf-sub {font-family:'Space Mono',monospace;font-size:11px;color:#a0a9b7;background:#121820;border:1px solid #252e3a;padding:7px 12px;border-radius:7px;margin-left:15px;}
.tf-eyebrow {font-size:12px;color:#9ba6b6;margin:4px 0 15px;}
.tf-jobtitle {font-size:19px;font-weight:800;color:#f0f4fa;margin-bottom:5px;}
.tf-muted {color:#a5afbd;font-size:13px;}
.tf-source {font-size:11px;color:#94a4b8;background:#222a35;border-radius:5px;padding:3px 7px;}
.tf-score {color:#69edb2;font-weight:800;font-size:16px;}
.tf-detailtitle {font-size:30px;font-weight:800;line-height:1.18;margin:12px 0;}
.tf-count {color:#a8b1bf;font-size:14px;font-weight:700;margin:15px 0;}
.tf-section {font-size:17px;font-weight:800;margin:14px 0 7px;}
.tf-description {color:#d4dce7;font-size:14px;line-height:1.7;white-space:pre-wrap;overflow-wrap:anywhere;}
.stButton>button, .stDownloadButton>button, .stLinkButton>a {border-radius:7px!important;font-weight:700!important;}
.stButton>button[kind="primary"] {background:#eaf2fb!important;color:#0d1117!important;border-color:#eaf2fb!important;}
div[data-testid="stVerticalBlockBorderWrapper"] {background:#171c24;border:1px solid #272f3a;border-radius:11px;padding:3px;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.tf-selected) {background:#111e33;border-color:#dce9fb;}
.stTextInput input,.stSelectbox [data-baseweb="select"],.stNumberInput input {background:#171c24!important;color:#f1f5f9!important;border-color:#2a3440!important;}
.stTabs [data-baseweb="tab-list"] {gap:18px;}
.stTabs [data-baseweb="tab"] {color:#a7b2c1;}
.stTabs [aria-selected="true"] {color:#f3f7ff!important;}
</style>''', unsafe_allow_html=True)


def safe(s):
    return html.escape(str(s or ""))


def fetch_board(token):
    try:
        jobs = GreenhouseProvider(board_tokens=[token]).search(CandidateJobProfile())
        return token, [j.model_dump(mode="json") for j in jobs], None
    except Exception as exc:
        return token, [], type(exc).__name__


@st.cache_data(ttl=900, show_spinner=False)
def load_jobs():
    output, errors, seen = [], [], set()
    with ThreadPoolExecutor(max_workers=9) as pool:
        futures = [pool.submit(fetch_board, token) for token in BOARDS]
        for future in as_completed(futures):
            token, jobs, error = future.result()
            if error:
                errors.append(f"{token}: {error}")
            for job in jobs:
                identity = (job["source"], job["company"], job["external_id"])
                if identity not in seen:
                    seen.add(identity)
                    output.append(job)
    output.sort(key=lambda j: (j["company"].lower(), j["title"].lower()))
    return output, errors


def role_relevant(job_title, titles):
    """Conservative lexical role gate; avoids broad generic-word matches."""
    job = job_title.lower()
    tokens = set(re.findall(r"[a-z0-9]+", job))
    for target in titles:
        target_tokens = set(re.findall(r"[a-z0-9]+", target.lower()))
        distinctive = target_tokens - STOP
        if not distinctive:
            continue
        if distinctive.issubset(tokens):
            return True
        if len(distinctive) >= 2 and len(distinctive & tokens) / len(distinctive) >= 0.75:
            return True
    return False


def score_job(job, profile):
    try:
        return int(calculate_match_score(profile, DiscoveredJob.model_validate(job)))
    except Exception:
        return 0


def remote_job(job):
    loc = (job.get("location") or "").lower()
    return any(term in loc for term in ("remote", "anywhere", "work from home"))


st.markdown('\n<style>\n/* tf-pagination-v2 ?? dark commerce-inspired design */\n.stApp { background: #0d1117; color: #eaf0f7; }\n.block-container { max-width: 1480px !important; padding: 1.5rem 2rem 3.5rem !important; }\n[data-testid="stVerticalBlock"] { gap: 0.9rem; }\n[data-testid="stHorizontalBlock"] { gap: 1rem; align-items: start; }\n[data-testid="stVerticalBlockBorderWrapper"] > div { border-radius: 14px !important; border-color: #293442 !important; background: #151c26 !important; }\n[data-testid="stVerticalBlockBorderWrapper"] > div:hover { border-color: #3c5364 !important; }\n.stButton button, .stLinkButton a { min-height: 42px !important; border-radius: 10px !important; font-weight: 650 !important; }\n.stButton button[kind="primary"], .stLinkButton a[kind="primary"] { background: #42dca4 !important; color: #091a16 !important; border-color: #42dca4 !important; }\n[data-testid="stTextInput"] input, [data-testid="stSelectbox"] > div { min-height: 46px !important; border-radius: 10px !important; }\n[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 1.5rem; border-bottom: 1px solid #293442; }\n[data-testid="stTabs"] button[role="tab"] { padding: 0.8rem 0.3rem; font-weight: 650; }\n.tf-jobtitle { font-size: 18px !important; line-height: 1.4 !important; letter-spacing: -0.015em; }\n.tf-detailtitle { line-height: 1.25 !important; letter-spacing: -0.025em; }\n.tf-description { line-height: 1.75 !important; font-size: 14px !important; }\n.tf-page-divider { border-top: 1px solid #293442; margin: 28px 0 18px; }\n.tf-page-summary { color: #aab8c9; font-size: 13px; margin-bottom: 12px; }\n.tf-page-summary strong { color: #f0f5fa; font-weight: 700; }\n@media(max-width: 768px) {\n  .block-container { padding: 1rem 0.8rem 2.5rem !important; }\n  .tf-top { flex-wrap: wrap; gap: 12px; }\n  .tf-brand { font-size: 16px !important; }\n}\n</style>\n', unsafe_allow_html=True)

st.markdown('<div class="tf-top"><div><span class="tf-brand"><span>✦</span>TALENTFLOW AI</span><span class="tf-sub">DIRECT JOBS · RESUME MATCHING</span></div><span class="tf-muted">Browse &nbsp; / &nbsp; My Matches</span></div>', unsafe_allow_html=True)

with st.expander("✦ Upload resume for personalized matches", expanded=not bool(st.session_state.get("tf_profile"))):
    upload_col, options_col = st.columns([3, 2])
    with upload_col:
        resume = st.file_uploader("Resume (PDF or DOCX)", type=["pdf", "docx"], key="tf_resume")
    with options_col:
        st.caption("Your resume determines target roles and match scores. Browsing works without it.")
        analyze = st.button("Analyze resume & find matches", type="primary", disabled=resume is None, use_container_width=True)
    if analyze and resume:
        digest = hashlib.sha256(resume.getvalue()).hexdigest()
        if digest == st.session_state.get("tf_resume_digest") and st.session_state.get("tf_profile"):
            st.success("Using your previously analyzed resume.")
        else:
            try:
                with st.spinner("Analyzing resume once..."):
                    profile = profile_from_resume(filename=resume.name, file_bytes=resume.getvalue())
                st.session_state["tf_profile"] = profile.model_dump(mode="json")
                st.session_state["tf_resume_digest"] = digest
                st.session_state.pop("tf_scored_jobs", None)
                st.session_state.pop("tf_scored_digest", None)
                st.session_state.pop("tf_external_jobs", None)
                st.session_state.pop("tf_external_digest", None)
                st.success("Resume analyzed. Open My Matches below.")
            except Exception as exc:
                st.error(f"Resume analysis unavailable: {type(exc).__name__}: {exc}")

with st.spinner("Loading company job boards..."):
    jobs, errors = load_jobs()

if errors:
    with st.expander(f"{len(errors)} source(s) temporarily unavailable"):
        st.write(errors)

if not jobs:
    st.warning("No job listings were retrieved. Check network access and retry.")
    if st.button("Retry loading"):
        load_jobs.clear()
        st.rerun()
    st.stop()

profile_data = st.session_state.get("tf_profile")

if profile_data:
    st.caption(
        "Personalized discovery: search additional job postings "
        "using your resume. TheirStack API credits may apply."
    )

    if st.button(
        "? Find Matching Jobs",
        key="tf_find_external_matches",
        type="primary",
    ):
        digest = st.session_state.get("tf_resume_digest")

        if (
            digest
            and digest == st.session_state.get("tf_external_digest")
        ):
            st.info(
                "Previously fetched jobs are already available. "
                "Upload a different resume to start a new search."
            )
        else:
            try:
                import os

                if not os.getenv("THEIRSTACK_API_KEY"):
                    st.error(
                        "THEIRSTACK_API_KEY is missing. "
                        "Configure it in .env before searching."
                    )
                else:
                    with st.spinner(
                        "Searching for resume-relevant openings..."
                    ):
                        profile = CandidateJobProfile.model_validate(
                            profile_data
                        )
                        provider = TheirStackProvider(limit=10)
                        discovered = provider.search(profile)

                        external = [
                            job.model_dump(mode="json")
                            for job in discovered
                        ]

                    st.session_state["tf_external_jobs"] = external
                    st.session_state["tf_external_digest"] = digest
                    st.session_state.pop("tf_scored_digest", None)

                    st.success(
                        f"Retrieved {len(external)} additional "
                        "job postings. Open My Matches below."
                    )

            except Exception as exc:
                st.error(
                    "Job discovery failed: "
                    f"{type(exc).__name__}: {exc}"
                )

tab_browse, tab_matches = st.tabs([f"Browse Jobs · {len(jobs):,}", "✦ My Matches · 80%+"])


def board(items, prefix, match_mode=False):
    if match_mode and not profile_data:
        st.info("Upload and analyze a resume above to see personalized matches.")
        return
    if match_mode:
        profile = CandidateJobProfile.model_validate(profile_data)
        fingerprint = st.session_state.get("tf_resume_digest")
        if st.session_state.get("tf_scored_digest") != fingerprint:
            with st.spinner("Calculating relevant matches..."):
                scored = []
                candidates = jobs + st.session_state.get(
                    "tf_external_jobs", []
                )
                seen_urls = set()

                for job in candidates:
                    url = str(job.get("job_url") or "").rstrip("/").lower()
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    if not role_relevant(job["title"], profile.target_titles):
                        continue
                    score = score_job(job, profile)
                    if score >= 80:
                        scored.append({**job, "_score": score})
                scored.sort(key=lambda j: j["_score"], reverse=True)
                st.session_state["tf_scored_jobs"] = scored
                st.session_state["tf_scored_digest"] = fingerprint
        items = st.session_state.get("tf_scored_jobs", [])

    q_col, loc_col, search_col = st.columns([6, 2, 1])
    with q_col:
        query = st.text_input("Search", placeholder="Search by job title, company or location (all words must match)", key=prefix+"q", label_visibility="collapsed")
    with loc_col:
        country = st.selectbox("Location", ["All locations", "United States", "Remote"], key=prefix+"country", label_visibility="collapsed")
    with search_col:
        st.button("Search", key=prefix+"search", type="primary", use_container_width=True)

    f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
    with f1:
        remote = st.checkbox("Remote only", key=prefix+"remote")
    with f2:
        company = st.selectbox("Company", ["All companies"] + sorted({j["company"] for j in items}), key=prefix+"company")
    with f3:
        sort = st.selectbox("Sort", ["Best match", "Company A-Z", "Title A-Z"] if match_mode else ["Title A-Z", "Company A-Z"], key=prefix+"sort")
    with f4:
        if st.button("Refresh jobs", key=prefix+"refresh"):
            load_jobs.clear()
            st.session_state.pop("tf_scored_digest", None)
            st.rerun()

    filtered = []
    for job in items:
        if company != "All companies" and job["company"] != company:
            continue
        if remote and not remote_job(job):
            continue
        location = (job.get("location") or "").lower()
        if country == "Remote" and not remote_job(job):
            continue
        if country == "United States" and not ("united states" in location or "usa" in location or re.search(r"(?:^|[,; ]\s*)(?:TX|CA|NY|WA|FL|MA|IL|CO|GA|NC|VA|NJ|AZ|OR|PA|OH|MI|MN|TN|UT|MD|CT|WI|MO|IN|DC)(?:$|[,; ])", job.get("location") or "")):
            continue
        title = str(job.get("title") or "").lower()
        terms = query.lower().split()
        synonyms = {
            "developer": ("developer", "engineer", "programmer"),
            "engineer": ("engineer", "developer"),
            "software": ("software", "backend", "frontend", "fullstack", "full-stack", "application"),
        }
        if not all(
            any(word in title for word in synonyms.get(term, (term,)))
            for term in terms
        ):
            continue
        filtered.append(job)
    if sort == "Company A-Z":
        filtered.sort(key=lambda j: (j["company"].lower(), j["title"].lower()))
    elif sort == "Title A-Z":
        filtered.sort(key=lambda j: j["title"].lower())

    st.markdown(f'<div class="tf-count">{"Resume matches ≥80%" if match_mode else "All direct jobs"} · {len(filtered):,} results</div>', unsafe_allow_html=True)
    if not filtered:
        st.info("No jobs meet the 80% role-relevant threshold from the current sources." if match_mode else "No jobs match the filters.")
        return

    page_size = 15
    pages = max(1, math.ceil(len(filtered) / page_size))
    page_key = prefix + "page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    if st.session_state[page_key] > pages:
        st.session_state[page_key] = pages
    if st.session_state[page_key] < 1:
        st.session_state[page_key] = 1
    page = int(st.session_state[page_key])
    shown = filtered[(page-1)*page_size:page*page_size]
    selected_key = prefix+"selected"
    ids = {f'{j["source"]}:{j["company"]}:{j["external_id"]}' for j in shown}
    if st.session_state.get(selected_key) not in ids:
        st.session_state[selected_key] = f'{shown[0]["source"]}:{shown[0]["company"]}:{shown[0]["external_id"]}'

    left, right = st.columns([0.95, 1.45], gap="medium")
    with left:
        st.caption("JOB LISTINGS")
        for job in shown:
            jid = f'{job["source"]}:{job["company"]}:{job["external_id"]}'
            selected = jid == st.session_state[selected_key]
            with st.container(border=True):
                if selected:
                    st.markdown('<div class="tf-selected"></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="tf-jobtitle">{safe(job["title"])}</div><div class="tf-muted">{safe(job["company"].title())}</div><div class="tf-muted" style="margin-top:10px">{safe(job.get("location") or "Location unspecified")}</div>', unsafe_allow_html=True)
                st.markdown(f'<span class="tf-source">via {safe(job["source"]).title()}</span>' + (f' &nbsp; <span class="tf-score">{job["_score"]}% match</span>' if match_mode else ''), unsafe_allow_html=True)
                if st.button("Selected ✓" if selected else "View details", key=prefix+jid, use_container_width=True):
                    st.session_state[selected_key] = jid
                    st.rerun()
    with right:
        selected = next(j for j in shown if f'{j["source"]}:{j["company"]}:{j["external_id"]}' == st.session_state[selected_key])
        with st.container(border=True):
            st.markdown(f'<div class="tf-muted">{safe(selected["company"].title())} &nbsp; <span class="tf-source">via {safe(selected["source"]).title()}</span></div><div class="tf-detailtitle">{safe(selected["title"])}</div><div class="tf-muted">⌖ &nbsp; {safe(selected.get("location") or "Location unspecified")}</div>', unsafe_allow_html=True)
            if match_mode:
                st.markdown(f'<div class="tf-score" style="margin-top:16px">✦ Resume match: {selected["_score"]}%</div>', unsafe_allow_html=True)
            st.link_button("Apply Direct ↗", str(selected["job_url"]), type="primary")
            st.divider()
            st.markdown('<div class="tf-section">Role Overview</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tf-description">{safe(selected.get("description") or "No job description supplied.")}</div>', unsafe_allow_html=True)
    # tf-pagination-v2: controls appear AFTER the listing/detail columns.
    st.markdown('<div class="tf-page-divider"></div>', unsafe_allow_html=True)
    first_result = (page - 1) * page_size + 1
    last_result = min(page * page_size, len(filtered))
    st.markdown(
        f'<div class="tf-page-summary">Showing <strong>{first_result:,} - {last_result:,}</strong> of <strong>{len(filtered):,}</strong> jobs</div>',
        unsafe_allow_html=True,
    )
    # Use stable keys and a callback so page state updates before rendering.
    def go_to_page(target):
        st.session_state[page_key] = max(1, min(pages, int(target)))
        st.session_state.pop(prefix + "selected", None)
    
    visible_pages = sorted(set(
        [1, pages] + list(range(max(1, page - 2), min(pages, page + 2) + 1))
    ))
    nav_columns = st.columns([1.35] + [0.7] * len(visible_pages) + [1.35], gap="small")
    with nav_columns[0]:
        st.button("Previous", key=prefix + "prev", disabled=page == 1,
                  on_click=go_to_page, args=(page - 1,), use_container_width=True)
    for index, number in enumerate(visible_pages, start=1):
        with nav_columns[index]:
            st.button(str(number), key=prefix + "pg_" + str(number),
                      type="primary" if number == page else "secondary",
                      disabled=number == page, on_click=go_to_page,
                      args=(number,), use_container_width=True)
    with nav_columns[-1]:
        st.button("Next", key=prefix + "next", disabled=page == pages,
                  on_click=go_to_page, args=(page + 1,), use_container_width=True)
    st.caption("Listings cached for 15 minutes ?? Match scores are estimates, not employer ATS scores")
with tab_browse:
    board(jobs, "browse_", False)
with tab_matches:
    board(jobs, "match_", True)

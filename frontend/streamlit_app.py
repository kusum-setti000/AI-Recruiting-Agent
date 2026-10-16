"""TalentFlow AI — Rocket-inspired Streamlit screening studio."""
import os
from datetime import datetime
from html import escape
import requests
import streamlit as st

st.set_page_config(page_title="TalentFlow AI | Screening Studio", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8002/analyze-candidate")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700;800;900&display=swap');
:root { --bg:#100e19; --panel:#201b2b; --panel2:#2a2237; --border:#4c415b; --text:#f7f4fc; --muted:#bcb3c9; --red:#f04452; --redbright:#ff6873; }
html,body,[data-testid="stApp"] {font-family:'Barlow',sans-serif!important;}
[data-testid="stAppViewContainer"],[data-testid="stMain"] {background:var(--bg)!important;color:var(--text)!important;}
.block-container {max-width:1450px;padding-top:1.8rem;padding-bottom:3rem;}
[data-testid="stSidebar"] {background:#171321!important;border-right:1px solid var(--border);}
[data-testid="stSidebar"] * {color:#f1edf6!important;}
[data-testid="stSidebar"] hr,[data-testid="stMain"] hr {border-color:var(--border)!important;}
[data-testid="stSidebar"] h2 {font-family:'Barlow Condensed',sans-serif!important;font-size:2rem!important;font-weight:900!important;letter-spacing:.04em;}
[data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3,[data-testid="stMain"] h4 {font-family:'Barlow Condensed',sans-serif!important;font-weight:800!important;letter-spacing:.02em;text-transform:uppercase;color:var(--text)!important;}
[data-testid="stMain"] h3 {color:#e7d9f3!important;}
[data-testid="stMain"] p,[data-testid="stMain"] li,[data-testid="stMain"] label,[data-testid="stMain"] [data-testid="stCaptionContainer"] {color:var(--muted)!important;}
[data-testid="stMain"] [data-testid="stWidgetLabel"] p {color:var(--text)!important;font-weight:700;}
.rocket-nav {display:block;padding:13px 12px;margin:4px 0;border-left:3px solid transparent;color:#a9a3b3!important;font-family:'Barlow Condensed',sans-serif;font-size:1.12rem;font-weight:700;letter-spacing:.07em;transition:color .22s,background .22s,border-color .22s,padding-left .22s;}
.rocket-nav:hover {color:var(--redbright)!important;background:rgba(240,68,82,.1);border-left-color:var(--red);padding-left:20px;}
.rocket-nav.active {color:#fff!important;border-left-color:var(--red);background:rgba(240,68,82,.13);}
.rocket-breadcrumb {display:flex;flex-wrap:wrap;gap:11px;align-items:center;margin-bottom:16px;font-family:'Barlow Condensed',sans-serif;font-size:.98rem;font-weight:700;letter-spacing:.11em;}
.rocket-breadcrumb span {color:#a9a3b3!important;transition:color .2s;}
.rocket-breadcrumb span:hover {color:var(--redbright)!important;}
.rocket-breadcrumb .current {color:#fff!important;}
.hero {background:radial-gradient(ellipse at 90% 0%,rgba(240,68,82,.20),transparent 50%),linear-gradient(110deg,#21192d,#322039 65%,#481c37);border:1px solid #6b405b;border-radius:16px;padding:38px 36px;margin-bottom:28px;box-shadow:0 16px 40px rgba(0,0,0,.2);}
.hero .eyebrow {font-family:'Barlow Condensed',sans-serif;font-size:.94rem;font-weight:800;letter-spacing:.18em;color:#ff919b!important;margin-bottom:14px;}
.hero h1 {font-family:'Barlow Condensed',sans-serif!important;font-size:clamp(3.2rem,5.5vw,5.8rem)!important;line-height:.98!important;font-weight:900!important;letter-spacing:.005em!important;color:#fff!important;margin:0 0 20px;text-transform:uppercase;}
.hero h1 em {font-style:normal;color:#ff6675!important;}
.hero p {color:#e2dbe9!important;font-size:1.08rem;line-height:1.6;margin:0;max-width:760px;}
[data-testid="stForm"] {background:var(--panel)!important;border:1px solid var(--border)!important;border-radius:15px!important;padding:20px;}
[data-testid="stMain"] input,[data-testid="stMain"] textarea {background:#2b2538!important;color:#fff!important;-webkit-text-fill-color:#fff!important;border:1px solid #665875!important;border-radius:9px!important;font-family:'Barlow',sans-serif!important;transition:border-color .2s,box-shadow .2s;}
[data-testid="stMain"] input::placeholder,[data-testid="stMain"] textarea::placeholder {color:#b2a5c0!important;-webkit-text-fill-color:#b2a5c0!important;}
[data-testid="stMain"] input:hover,[data-testid="stMain"] textarea:hover {border-color:var(--red)!important;}
[data-testid="stMain"] input:focus,[data-testid="stMain"] textarea:focus {border-color:var(--red)!important;box-shadow:0 0 0 2px rgba(240,68,82,.22)!important;}
[data-testid="stFileUploaderDropzone"] {background:#2b2538!important;border:1px dashed #9b829d!important;border-radius:10px!important;transition:border-color .2s;}
[data-testid="stFileUploaderDropzone"]:hover {border-color:var(--red)!important;}
[data-testid="stFileUploaderDropzone"] * {color:#e9e2ef!important;}
[data-testid="stFormSubmitButton"] button {background:linear-gradient(100deg,#af233e,#f04452)!important;border:0!important;border-radius:9px!important;min-height:49px;transition:transform .2s,filter .2s;}
[data-testid="stFormSubmitButton"] button:hover {filter:brightness(1.15);transform:translateY(-2px);}
[data-testid="stFormSubmitButton"] button * {color:#fff!important;font-weight:800!important;}
[data-testid="stMetric"] {background:var(--panel2)!important;border:1px solid var(--border)!important;border-radius:12px!important;padding:15px;}
[data-testid="stMetric"] * {color:#eae4f0!important;}
[data-testid="stMetricValue"] {font-family:'Barlow Condensed',sans-serif!important;font-weight:900!important;color:#ff8290!important;}
[data-testid="stMain"] button[data-baseweb="tab"] p {color:#bcb3c9!important;font-family:'Barlow Condensed',sans-serif!important;font-size:1.12rem!important;font-weight:800!important;letter-spacing:.04em;transition:color .2s;}
[data-testid="stMain"] button[data-baseweb="tab"]:hover p {color:var(--redbright)!important;}
[data-testid="stMain"] button[data-baseweb="tab"][aria-selected="true"] p {color:#fff!important;}
[data-testid="stDownloadButton"] button {background:#342537!important;border:1px solid #985367!important;border-radius:9px!important;}
[data-testid="stDownloadButton"] button:hover {background:var(--red)!important;border-color:var(--red)!important;}
[data-testid="stDownloadButton"] button * {color:#fff!important;font-weight:700;}
[data-testid="stSidebar"] button {background:#342537!important;border:1px solid #67465c!important;}
[data-testid="stSidebar"] button:hover {background:#9f2c43!important;}
[data-testid="stMain"] button:focus-visible {outline:2px solid var(--redbright);outline-offset:3px;}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px!important;}
@media (prefers-reduced-motion:reduce) {.rocket-nav,[data-testid="stMain"] button,[data-testid="stMain"] input,[data-testid="stMain"] textarea {transition:none!important;}}
</style>
""", unsafe_allow_html=True)

if "screening_result" not in st.session_state:
    st.session_state.screening_result = None
if "screening_error" not in st.session_state:
    st.session_state.screening_error = None


def list_field(analysis, key):
    value = analysis.get(key) or []
    return value if isinstance(value, list) else []


def show_bullets(items, empty_message):
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.info(empty_message)


def report_text(result, analysis, score, assessment):
    lines = [
        "TALENTFLOW AI | SCREENING REPORT",
        f"Generated: {datetime.now():%Y-%m-%d %H:%M}",
        f"Role: {result.get('job_title', '')}",
        f"Resume: {result.get('candidate_resume', '')}",
        f"Alignment estimate: {score}%",
        f"Assessment: {assessment}",
        "\nASSESSMENT REASONING\n" + str(analysis.get("assessment_reasoning", "")),
        "\nEXPERIENCE ALIGNMENT\n" + str(analysis.get("experience_alignment", "")),
    ]
    for heading, key in [
        ("MATCHING SKILLS", "matching_skills"),
        ("MISSING OR UNVERIFIED SKILLS", "missing_skills"),
        ("CANDIDATE STRENGTHS", "candidate_strengths"),
        ("POTENTIAL GAPS", "potential_gaps"),
        ("RECRUITER QUESTIONS", "recruiter_questions"),
    ]:
        lines.append("\n" + heading)
        lines.extend("- " + str(item) for item in list_field(analysis, key))
    lines.append("\nAI-generated decision support. Human review required.")
    return "\n".join(lines)


with st.sidebar:
    st.markdown("## ✦ TalentFlow AI")
    st.caption("RECRUITMENT INTELLIGENCE")
    st.divider()
    st.markdown("""
<div class="rocket-nav active">01 / SCREENING STUDIO</div>
<div class="rocket-nav">02 / RESUME HISTORY — SOON</div>
<div class="rocket-nav">03 / CANDIDATE PROFILES — SOON</div>
<div class="rocket-nav">04 / JOB LIBRARY — SOON</div>
<div class="rocket-nav">05 / ANALYTICS — SOON</div>
""", unsafe_allow_html=True)
    st.divider()
    st.caption("BACKEND CONNECTION")
    if st.button("Check API status", use_container_width=True):
        try:
            response = requests.get(API_URL.rsplit("/", 1)[0] + "/openapi.json", timeout=5)
            if response.ok:
                st.success("API is reachable")
            else:
                st.warning(f"API returned HTTP {response.status_code}")
        except requests.RequestException:
            st.error("Cannot reach FastAPI. Check port 8002.")
    st.caption("AI-assisted screening · Human-reviewed decisions")

st.markdown("""
<div class="rocket-breadcrumb">
    <span>TALENTFLOW</span><span>/</span>
    <span>RECRUITMENT INTELLIGENCE</span><span>/</span>
    <span class="current">SCREENING STUDIO</span>
</div>
<div class="hero">
    <div class="eyebrow">TALENTFLOW / AI SCREENING STUDIO</div>
    <h1>DISCOVER TALENT.<br><em>DECODE POTENTIAL.</em></h1>
    <p>Precision candidate screening. Evidence-based intelligence. Human-led decisions.</p>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1, 1.12], gap="large")

with left:
    st.markdown("### New candidate analysis")
    st.caption("Provide the role and upload a resume to begin.")
    with st.form("screening_form", clear_on_submit=False):
        job_title = st.text_input("Job title *", placeholder="e.g., Senior AI/ML Engineer")
        job_description = st.text_area("Job description *", height=235, placeholder="Paste the responsibilities, qualifications, and required skills...")
        uploaded_file = st.file_uploader("Candidate resume *", type=["pdf", "docx"])
        st.caption("The job title and description are checked for alignment before scoring.")
        submitted = st.form_submit_button("✦ Analyze candidate", type="primary", use_container_width=True)

    if submitted:
        st.session_state.screening_result = None
        st.session_state.screening_error = None
        if not job_title.strip():
            st.session_state.screening_error = "Enter a job title."
        elif not job_description.strip():
            st.session_state.screening_error = "Enter a job description."
        elif uploaded_file is None:
            st.session_state.screening_error = "Upload a PDF or DOCX resume."
        else:
            with st.spinner("Validating the role and analyzing the resume..."):
                try:
                    response = requests.post(
                        API_URL,
                        data={"job_title": job_title.strip(), "job_description": job_description.strip()},
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")},
                        timeout=180,
                    )
                    try:
                        payload = response.json()
                    except ValueError:
                        payload = {"detail": "The API returned a non-JSON response."}
                    if response.ok and isinstance(payload, dict):
                        alignment = payload.get("job_alignment") or {}
                        analysis = payload.get("ai_analysis")
                        if isinstance(alignment, dict) and alignment.get("status") not in (None, "aligned"):
                            st.session_state.screening_error = "Job title and description need review: " + str(alignment.get("reason", "Please clarify the role."))
                        elif isinstance(analysis, dict):
                            st.session_state.screening_result = payload
                        else:
                            st.session_state.screening_error = "The API returned no candidate analysis. " + str(payload.get("message") or payload.get("detail") or "Review the backend response.")
                    else:
                        detail = payload.get("detail", payload.get("message", "Unknown error")) if isinstance(payload, dict) else str(payload)
                        if isinstance(detail, dict):
                            detail = detail.get("message") or detail.get("reason") or str(detail)
                        st.session_state.screening_error = f"API error ({response.status_code}): {detail}"
                except requests.exceptions.Timeout:
                    st.session_state.screening_error = "Analysis timed out after 180 seconds. Check backend logs."
                except requests.exceptions.ConnectionError:
                    st.session_state.screening_error = "Cannot connect to FastAPI at port 8002."
                except requests.RequestException as exc:
                    st.session_state.screening_error = f"Network error: {exc}"
    if st.session_state.screening_error:
        st.error(st.session_state.screening_error)
        st.caption("No match score was generated for this request.")

with right:
    st.markdown("### Candidate intelligence")
    st.caption("Your screening report appears here after analysis.")
    result = st.session_state.screening_result
    if result is None:
        with st.container(border=True):
            st.markdown("### ◎ Ready when you are")
            st.write("Enter a job description and upload a resume to generate an evidence-based screening report.")
        c1, c2 = st.columns(2)
        c1.metric("Skills evaluated", "—")
        c2.metric("Match estimate", "—")
    else:
        analysis = result["ai_analysis"]
        try:
            score = max(0, min(100, int(analysis.get("match_score", 0))))
        except (ValueError, TypeError):
            score = 0
        assessment = str(analysis.get("overall_assessment", "Needs Human Review"))
        with st.container(border=True):
            st.caption("RESUME ALIGNMENT ESTIMATE")
            st.markdown(f"# {score}%")
            st.markdown(f"**{assessment}**")
            st.progress(score / 100)
            st.caption("AI-generated estimate, not a prediction of hiring success.")
        matching = list_field(analysis, "matching_skills")
        missing = list_field(analysis, "missing_skills")
        m1, m2 = st.columns(2)
        m1.metric("Matching skills", len(matching))
        m2.metric("Missing / unverified", len(missing))
        st.caption(f"Resume: {result.get('candidate_resume', 'Uploaded document')} · Role: {result.get('job_title', '—')}")
        overview, skills, review = st.tabs(["Overview", "Skill evidence", "Recruiter review"])
        with overview:
            st.markdown("#### Assessment reasoning")
            st.write(analysis.get("assessment_reasoning") or "Not provided.")
            st.markdown("#### Experience alignment")
            st.write(analysis.get("experience_alignment") or "Not provided.")
            alignment = result.get("job_alignment") or {}
            if isinstance(alignment, dict):
                with st.expander("Job description alignment check"):
                    st.write(alignment.get("reason") or "No additional notes.")
        with skills:
            st.markdown("#### Matching skills")
            show_bullets(matching, "No verified matches identified.")
            st.markdown("#### Missing or unverified skills")
            show_bullets(missing, "No missing requirements identified.")
            st.markdown("#### Candidate strengths")
            show_bullets(list_field(analysis, "candidate_strengths"), "No strengths listed.")
        with review:
            st.markdown("#### Potential gaps")
            show_bullets(list_field(analysis, "potential_gaps"), "No additional gaps listed.")
            st.markdown("#### Recruiter questions")
            questions = list_field(analysis, "recruiter_questions")
            if questions:
                for i, question in enumerate(questions, 1):
                    st.markdown(f"**{i}.** {question}")
            else:
                st.info("No interview questions listed.")
        st.download_button("↓ Download screening report", data=report_text(result, analysis, score, assessment), file_name="talentflow_screening_report.txt", mime="text/plain", use_container_width=True)

st.divider()
st.caption("TalentFlow AI · Decision support only. Assess candidates using job-relevant evidence and human review.")

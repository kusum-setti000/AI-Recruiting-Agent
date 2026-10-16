
import logging
import os
import shutil
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.models.schemas import JobDescription
from app.services.llm_service import validate_job_alignment
from app.services.screening_graph import run_screening_graph
from app.services.resume_parser import extract_resume_text


# ==========================================================
# 1. APPLICATION CONFIGURATION
# ==========================================================

logger = logging.getLogger(__name__)

app = FastAPI(
    title="TalentFlow AI Recruiting Agent",
    description=(
        "AI-powered resume screening using "
        "FastAPI, LangChain, and LangGraph"
    ),
    version="1.2.0",
)


# ==========================================================
# 2. VALIDATE RESUME FILE
# ==========================================================

def validate_resume_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No resume was uploaded.",
        )

    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )


# ==========================================================
# 3. EXTRACT RESUME TEXT
# ==========================================================

def read_resume(file: UploadFile) -> str:
    """
    Extract resume text from PDF or DOCX
    and remove the temporary file.
    """

    temporary_path = None

    try:
        suffix = os.path.splitext(file.filename)[1].lower()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temporary_file:
            temporary_path = temporary_file.name

            shutil.copyfileobj(
                file.file,
                temporary_file,
            )

        resume_text = extract_resume_text(
            temporary_path,
            file.filename,
        )

        if not resume_text or not resume_text.strip():
            raise HTTPException(
                status_code=422,
                detail=(
                    "No readable text was found in the resume. "
                    "Please upload a text-based PDF or DOCX."
                ),
            )

        return resume_text

    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


# ==========================================================
# 4. HOME ENDPOINT
# ==========================================================

@app.get("/")
def home():
    return {
        "message": "TalentFlow AI Recruiting Agent is running",
        "version": app.version,
        "frameworks": [
            "FastAPI",
            "LangChain",
            "LangGraph",
        ],
    }


# ==========================================================
# 5. RESUME UPLOAD ENDPOINT
# ==========================================================

@app.post("/upload-resume")
def upload_resume(
    file: UploadFile = File(...),
):
    validate_resume_file(file)

    try:
        extracted_text = read_resume(file)

        return {
            "filename": file.filename,
            "extracted_text": extracted_text,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Resume extraction failed")

        raise HTTPException(
            status_code=500,
            detail=(
                "Resume extraction failed. "
                "Check the backend terminal for details."
            ),
        )


# ==========================================================
# 6. JOB DESCRIPTION ENDPOINT
# ==========================================================

@app.post("/job-description")
def receive_job_description(
    job: JobDescription,
):
    job_title = job.job_title.strip()
    job_description = job.job_description.strip()

    if not job_title or not job_description:
        raise HTTPException(
            status_code=422,
            detail=(
                "Please provide a job title "
                "and job description."
            ),
        )

    return {
        "job_title": job_title,
        "job_description": job_description,
        "message": "Job description received successfully",
    }


# ==========================================================
# 7. CANDIDATE SCREENING ENDPOINT
#    FASTAPI -> LANGGRAPH -> LANGCHAIN -> OPENAI
# ==========================================================

@app.post("/analyze-candidate")
def analyze_candidate(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
):
    # Validate uploaded file type.
    validate_resume_file(file)

    # Normalize job inputs.
    job_title = job_title.strip()
    job_description = job_description.strip()

    if not job_title or not job_description:
        raise HTTPException(
            status_code=422,
            detail=(
                "Please provide a job title "
                "and job description."
            ),
        )

    try:
        # --------------------------------------------------
        # STEP 1: VALIDATE JOB TITLE AND DESCRIPTION
        # --------------------------------------------------

        alignment = validate_job_alignment(
            job_title=job_title,
            job_description=job_description,
        )

        # Stop if job title and description are inconsistent.
        if alignment.status != "aligned":
            raise HTTPException(
                status_code=422,
                detail={
                    "status": alignment.status,
                    "message": alignment.reason,
                },
            )

        # --------------------------------------------------
        # STEP 2: EXTRACT RESUME CONTENT
        # --------------------------------------------------

        resume_text = read_resume(file)

        # --------------------------------------------------
        # STEP 3: EXECUTE LANGGRAPH WORKFLOW
        # --------------------------------------------------

        result = run_screening_graph(
            job_title=job_title,
            job_description=job_description,
            resume_text=resume_text,
            prevalidated_alignment=alignment.model_dump(),
        )

        # --------------------------------------------------
        # STEP 4: VERIFY GRAPH ALIGNMENT RESULT
        # --------------------------------------------------

        graph_alignment = result["job_alignment"]

        if graph_alignment["status"] != "aligned":
            raise HTTPException(
                status_code=422,
                detail={
                    "status": graph_alignment["status"],
                    "message": graph_alignment["reason"],
                },
            )

        # --------------------------------------------------
        # STEP 5: EXTRACT AI SCREENING RESULT
        # --------------------------------------------------

        ai_analysis = result.get("ai_analysis")

        if ai_analysis is None:
            raise RuntimeError(
                "LangGraph did not return candidate analysis."
            )

        # --------------------------------------------------
        # STEP 6: RETURN RESULTS TO STREAMLIT
        # --------------------------------------------------

        return {
            "candidate_resume": file.filename,
            "job_title": job_title,
            "job_alignment": graph_alignment,
            "ai_analysis": ai_analysis,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Candidate analysis failed")

        raise HTTPException(
            status_code=500,
            detail=(
                "Candidate analysis failed. "
                "Check the backend terminal for details."
            ),
        )

import logging
import os
import shutil
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.models.schemas import JobDescription
from app.prompts.screening_prompt import build_screening_prompt
from app.services.llm_service import (
    analyze_with_llm,
    validate_job_alignment,
)
from app.services.resume_parser import extract_resume_text


logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Recruiting Agent",
    description="Resume analysis using a job title and job description",
    version="1.1.0",
)


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


def read_resume(file: UploadFile) -> str:
    """Extract resume text and remove the temporary file."""

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


@app.get("/")
def home():
    return {
        "message": "AI Recruiting Agent is running",
        "version": app.version,
    }


@app.post("/upload-resume")
def upload_resume(file: UploadFile = File(...)):
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


@app.post("/job-description")
def receive_job_description(job: JobDescription):
    job_title = job.job_title.strip()
    job_description = job.job_description.strip()

    if not job_title or not job_description:
        raise HTTPException(
            status_code=422,
            detail="Please provide a job title and job description.",
        )

    return {
        "job_title": job_title,
        "job_description": job_description,
        "message": "Job description received successfully",
    }


@app.post("/analyze-candidate")
def analyze_candidate(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
):
    validate_resume_file(file)

    job_title = job_title.strip()
    job_description = job_description.strip()

    if not job_title or not job_description:
        raise HTTPException(
            status_code=422,
            detail="Please provide a job title and job description.",
        )

    try:
        # Validate the job title against the JD first.
        alignment = validate_job_alignment(
            job_title=job_title,
            job_description=job_description,
        )

        # Stop before candidate analysis if the role is inconsistent
        # or there is insufficient information.
        if alignment.status != "aligned":
            raise HTTPException(
                status_code=422,
                detail={
                    "status": alignment.status,
                    "message": alignment.reason,
                },
            )

        resume_text = read_resume(file)

        # Include all three inputs in the candidate analysis prompt.
        screening_prompt = build_screening_prompt(
            resume_text=resume_text,
            job_description=job_description,
            job_title=job_title,
        )

        ai_analysis = analyze_with_llm(screening_prompt)

        return {
            "candidate_resume": file.filename,
            "job_title": job_title,
            "job_alignment": alignment.model_dump(),
            "ai_analysis": ai_analysis.model_dump(),
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
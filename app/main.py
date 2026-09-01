from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from app.services.resume_parser import extract_resume_text
from app.models.schemas import JobDescription
from app.prompts.screening_prompt import build_screening_prompt
from app.services.llm_service import analyze_with_llm

import os
import shutil
import tempfile


# Create the FastAPI application
app = FastAPI(
    title="AI Recruiting Agent",
    description="Code-first AI agent for resume and job description analysis",
    version="1.0.0"
)


# ---------------------------------------------------
# 1. HOME ENDPOINT
# ---------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "AI Recruiting Agent is running"
    }


# ---------------------------------------------------
# 2. RESUME UPLOAD ENDPOINT
# ---------------------------------------------------

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was uploaded."
        )

    if not (
        file.filename.lower().endswith(".pdf")
        or file.filename.lower().endswith(".docx")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported."
        )

    temporary_path = None

    try:
        suffix = os.path.splitext(file.filename)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temporary_file:

            shutil.copyfileobj(
                file.file,
                temporary_file
            )

            temporary_path = temporary_file.name

        extracted_text = extract_resume_text(
            temporary_path,
            file.filename
        )

        return {
            "filename": file.filename,
            "extracted_text": extracted_text
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


# ---------------------------------------------------
# 3. JOB DESCRIPTION ENDPOINT
# ---------------------------------------------------

@app.post("/job-description")
def receive_job_description(job: JobDescription):

    return {
        "job_title": job.job_title,
        "job_description": job.job_description,
        "message": "Job description received successfully"
    }


# ---------------------------------------------------
# # ---------------------------------------------------
# 4. ANALYZE CANDIDATE ENDPOINT
# ---------------------------------------------------

@app.post("/analyze-candidate")
async def analyze_candidate(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No resume was uploaded."
        )

    if not (
        file.filename.lower().endswith(".pdf")
        or file.filename.lower().endswith(".docx")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported."
        )

    temporary_path = None

    try:
        suffix = os.path.splitext(file.filename)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temporary_file:

            shutil.copyfileobj(
                file.file,
                temporary_file
            )

            temporary_path = temporary_file.name

        resume_text = extract_resume_text(
            temporary_path,
            file.filename
        )

        screening_prompt = build_screening_prompt(
            resume_text,
            job_description
        )

        ai_analysis = analyze_with_llm(
            screening_prompt
        )

        return {
            "candidate_resume": file.filename,
            "job_title": job_title,
            "ai_analysis": ai_analysis
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
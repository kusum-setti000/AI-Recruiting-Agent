"""FastAPI endpoints for resume-based job discovery."""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.agents.document_loader import ResumeValidationError
from app.integrations.job_discovery.resume_profiler import profile_from_resume
from app.integrations.job_discovery.service import JobDiscoveryService

app = FastAPI(title="AI Recruiting Agent")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/jobs/discover-from-resume")
async def discover_from_resume(
    resume: UploadFile = File(...),
    location: str | None = Form(default=None),
    remote_only: bool = Form(default=False),
):
    try:
        file_bytes = await resume.read()

        profile = profile_from_resume(
            filename=resume.filename or "",
            file_bytes=file_bytes,
            location=location,
            remote_only=remote_only,
        )

        result = JobDiscoveryService().search(profile)

        return {
            "candidate_profile": profile.model_dump(),
            "total_found": result.total_found,
            "jobs": [job.model_dump(mode="json") for job in result.jobs],
        }

    except ResumeValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

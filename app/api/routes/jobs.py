
from fastapi import APIRouter, HTTPException

from app.models.schemas import JobDescription


router = APIRouter(tags=["Jobs"])


@router.post("/job-description")
def receive_job_description(job: JobDescription):

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

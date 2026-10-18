
import logging

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.services.llm_service import validate_job_alignment
from app.services.screening_graph import run_screening_graph
from app.services.resume_service import (
    read_resume,
    validate_resume_file,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Screening"])


@router.post("/analyze-candidate")
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
        # 1. Validate job alignment
        alignment = validate_job_alignment(
            job_title=job_title,
            job_description=job_description,
        )

        if alignment.status != "aligned":
            raise HTTPException(
                status_code=422,
                detail={
                    "status": alignment.status,
                    "message": alignment.reason,
                },
            )

        # 2. Extract resume text
        resume_text = read_resume(file)

        # 3. Execute LangGraph
        result = run_screening_graph(
            job_title=job_title,
            job_description=job_description,
            resume_text=resume_text,
            prevalidated_alignment=alignment.model_dump(),
        )

        # 4. Validate graph result
        graph_alignment = result["job_alignment"]

        if graph_alignment["status"] != "aligned":
            raise HTTPException(
                status_code=422,
                detail={
                    "status": graph_alignment["status"],
                    "message": graph_alignment["reason"],
                },
            )

        # 5. Retrieve candidate analysis
        ai_analysis = result.get("ai_analysis")

        if ai_analysis is None:
            raise RuntimeError(
                "LangGraph did not return candidate analysis."
            )

        # 6. Return response
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

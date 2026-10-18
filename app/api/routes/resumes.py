
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.resume_service import (
    read_resume,
    validate_resume_file,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Resumes"])


@router.post("/upload-resume")
def upload_resume(file: UploadFile = File(...)):
    """Upload a PDF/DOCX resume and extract its text."""

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

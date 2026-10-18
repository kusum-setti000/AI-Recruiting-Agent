
import os
import tempfile
import zipfile
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.services.resume_parser import extract_resume_text


# Maximum supported resume size: 5 MB
MAX_RESUME_SIZE = 5 * 1024 * 1024

# Read uploaded files in 64 KB chunks
CHUNK_SIZE = 64 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def validate_resume_file(file: UploadFile) -> None:
    """
    Validate the uploaded resume filename and extension.

    File size and content validation happen in read_resume().
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No resume was uploaded.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )


def validate_file_content(
    file_path: str,
    extension: str,
) -> None:
    """
    Check that file content matches the expected format.

    This is basic format validation, not malware scanning.
    """

    if extension == ".pdf":
        with open(file_path, "rb") as uploaded_file:
            signature = uploaded_file.read(5)

        if signature != b"%PDF-":
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file content.",
            )

    elif extension == ".docx":
        try:
            with zipfile.ZipFile(file_path, "r") as archive:
                if "word/document.xml" not in archive.namelist():
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid DOCX file content.",
                    )

        except zipfile.BadZipFile as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid DOCX file content.",
            ) from exc


def read_resume(file: UploadFile) -> str:
    """
    Read and validate a resume before extracting text.

    Enforces:
    - PDF/DOCX extensions
    - 5 MB file size limit
    - Basic file-format validation
    - Temporary-file cleanup
    - Nonempty extracted text
    """

    validate_resume_file(file)

    extension = Path(file.filename).suffix.lower()
    temporary_path = None

    try:
        total_size = 0

        with tempfile.NamedTemporaryFile(
            mode="wb",
            delete=False,
            suffix=extension,
        ) as temporary_file:

            temporary_path = temporary_file.name

            while True:
                chunk = file.file.read(CHUNK_SIZE)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_RESUME_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "Resume exceeds the maximum "
                            "allowed size of 5 MB."
                        ),
                    )

                temporary_file.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded resume is empty.",
            )

        validate_file_content(
            temporary_path,
            extension,
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
        if temporary_path:
            try:
                os.remove(temporary_path)
            except FileNotFoundError:
                pass

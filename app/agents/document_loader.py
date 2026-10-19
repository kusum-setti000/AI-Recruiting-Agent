
"""Validate and extract resume text using LangChain document loaders."""

import tempfile
import zipfile
from pathlib import Path

import pymupdf
from langchain_community.document_loaders import Docx2txtLoader, PyMuPDFLoader

from app.agents.config import get_settings


class ResumeValidationError(ValueError):
    """Invalid or unsupported resume."""


def validate_resume_upload(filename: str, file_bytes: bytes) -> None:
    """Validate file type, size, and document structure."""
    settings = get_settings()

    if not isinstance(filename, str) or not filename.strip():
        raise ResumeValidationError("Resume filename is required.")

    if not isinstance(file_bytes, bytes) or not file_bytes:
        raise ResumeValidationError("Resume file is empty or invalid.")

    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".docx"}:
        raise ResumeValidationError("Only PDF and DOCX files are supported.")

    if len(file_bytes) > settings.max_resume_size_mb * 1024 * 1024:
        raise ResumeValidationError(
            f"Resume exceeds {settings.max_resume_size_mb} MB."
        )

    if extension == ".pdf":
        if not file_bytes.startswith(b"%PDF-"):
            raise ResumeValidationError("Invalid PDF file content.")

        try:
            with pymupdf.open(stream=file_bytes, filetype="pdf") as pdf:
                if pdf.needs_pass:
                    raise ResumeValidationError("Encrypted PDFs are not supported.")
                if not 1 <= pdf.page_count <= settings.max_resume_pages:
                    raise ResumeValidationError("Invalid PDF page count.")
        except ResumeValidationError:
            raise
        except Exception as exc:
            raise ResumeValidationError("Unreadable PDF file.") from exc

    else:
        try:
            with zipfile.ZipFile(__import__("io").BytesIO(file_bytes)) as docx:
                if "word/document.xml" not in docx.namelist():
                    raise ResumeValidationError("Invalid DOCX file content.")
                if any(info.flag_bits & 1 for info in docx.infolist()):
                    raise ResumeValidationError("Encrypted DOCX files are not supported.")
                if sum(info.file_size for info in docx.infolist()) > 50 * 1024 * 1024:
                    raise ResumeValidationError("DOCX expanded content is too large.")
        except zipfile.BadZipFile as exc:
            raise ResumeValidationError("Invalid DOCX file content.") from exc


def load_resume(filename: str, file_bytes: bytes) -> str:
    """Extract resume text, enforcing configured size limits."""
    validate_resume_upload(filename, file_bytes)

    settings = get_settings()
    extension = Path(filename).suffix.lower()

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / f"resume{extension}"
        path.write_bytes(file_bytes)

        loader = (
            PyMuPDFLoader(str(path), mode="page")
            if extension == ".pdf"
            else Docx2txtLoader(str(path))
        )

        parts = []
        length = 0

        try:
            for document in loader.lazy_load():
                text = document.page_content
                length += len(text)

                if length > settings.max_resume_characters:
                    raise ResumeValidationError("Resume text exceeds the allowed limit.")

                parts.append(text)
        except ResumeValidationError:
            raise
        except Exception as exc:
            raise ResumeValidationError("Unable to extract resume text.") from exc

    result = "\n\n".join(parts).strip()
    if not result:
        raise ResumeValidationError("Resume contains no extractable text.")

    return result

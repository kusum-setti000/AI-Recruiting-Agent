
from pathlib import Path

import pymupdf
from docx import Document
from fastapi import HTTPException


# Resource limits for resume processing
MAX_PDF_PAGES = 30
MAX_EXTRACTED_CHARACTERS = 100_000


def _limit_extracted_text(text: str) -> str:
    """
    Reject documents that exceed the supported
    extracted-text limit.

    Do not silently truncate candidate information.
    """

    if len(text) > MAX_EXTRACTED_CHARACTERS:
        raise HTTPException(
            status_code=413,
            detail=(
                "Resume contains too much text. "
                "Please upload a shorter document."
            ),
        )

    return text.strip()


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text from a text-based PDF.

    PDF documents are explicitly closed after processing.
    """

    try:
        with pymupdf.open(file_path) as document:

            if document.page_count > MAX_PDF_PAGES:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        "Resume exceeds the maximum "
                        f"of {MAX_PDF_PAGES} PDF pages."
                    ),
                )

            pages = []
            total_characters = 0

            for page in document:
                page_text = page.get_text("text")

                total_characters += len(page_text)

                if total_characters > MAX_EXTRACTED_CHARACTERS:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "Resume contains too much text. "
                            "Please upload a shorter document."
                        ),
                    )

                pages.append(page_text)

            return _limit_extracted_text(
                "\n".join(pages)
            )

    except HTTPException:
        raise

    except (
        pymupdf.FileDataError,
        pymupdf.EmptyFileError,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                "The PDF could not be read. "
                "Please upload a valid text-based PDF."
            ),
        ) from exc


def extract_docx_text(file_path: str) -> str:
    """
    Extract resume text from DOCX paragraphs and tables.

    Uses document order where supported by python-docx.
    """

    try:
        document = Document(file_path)

        sections = []
        total_characters = 0

        for block in document.iter_inner_content():

            if hasattr(block, "rows"):
                # Table
                for row in block.rows:
                    cells = [
                        cell.text.strip()
                        for cell in row.cells
                    ]

                    block_text = " | ".join(
                        cell for cell in cells if cell
                    )

                    if block_text:
                        sections.append(block_text)
                        total_characters += len(block_text)

            else:
                # Paragraph
                block_text = block.text.strip()

                if block_text:
                    sections.append(block_text)
                    total_characters += len(block_text)

            if total_characters > MAX_EXTRACTED_CHARACTERS:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        "Resume contains too much text. "
                        "Please upload a shorter document."
                    ),
                )

        return _limit_extracted_text(
            "\n".join(sections)
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                "The DOCX could not be read. "
                "Please upload a valid DOCX file."
            ),
        ) from exc


def extract_resume_text(
    file_path: str,
    filename: str,
) -> str:
    """
    Route resume extraction to the appropriate parser.
    """

    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(file_path)

    if extension == ".docx":
        return extract_docx_text(file_path)

    raise HTTPException(
        status_code=400,
        detail="Only PDF and DOCX resumes are supported.",
    )

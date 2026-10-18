
import io
import zipfile
from unittest.mock import patch

import pytest
from fastapi import HTTPException, UploadFile

from app.services.resume_service import (
    MAX_RESUME_SIZE,
    read_resume,
    validate_resume_file,
)


def make_upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
    )


def make_docx_bytes() -> bytes:
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            "<Types/>",
        )
        archive.writestr(
            "word/document.xml",
            "<document/>",
        )

    return buffer.getvalue()


def test_accept_pdf_extension():
    file = make_upload("resume.pdf", b"%PDF-1.7")
    validate_resume_file(file)


def test_accept_docx_extension():
    file = make_upload("resume.docx", make_docx_bytes())
    validate_resume_file(file)


@pytest.mark.parametrize(
    "filename",
    ["resume.txt", "resume.exe", "resume.doc", "resume"],
)
def test_reject_unsupported_extension(filename):
    file = make_upload(filename, b"test")

    with pytest.raises(HTTPException) as error:
        validate_resume_file(file)

    assert error.value.status_code == 400


def test_reject_missing_filename():
    file = make_upload("", b"test")

    with pytest.raises(HTTPException) as error:
        validate_resume_file(file)

    assert error.value.status_code == 400


def test_reject_empty_upload():
    file = make_upload("resume.pdf", b"")

    with pytest.raises(HTTPException) as error:
        read_resume(file)

    assert error.value.status_code == 400


def test_reject_oversized_upload():
    file = make_upload(
        "resume.pdf",
        b"x" * (MAX_RESUME_SIZE + 1),
    )

    with pytest.raises(HTTPException) as error:
        read_resume(file)

    assert error.value.status_code == 413


def test_reject_invalid_pdf_signature():
    file = make_upload("resume.pdf", b"not a pdf")

    with pytest.raises(HTTPException) as error:
        read_resume(file)

    assert error.value.status_code == 400


def test_reject_invalid_docx():
    file = make_upload("resume.docx", b"not a zip archive")

    with pytest.raises(HTTPException) as error:
        read_resume(file)

    assert error.value.status_code == 400


def test_accept_valid_pdf_content():
    file = make_upload(
        "resume.pdf",
        b"%PDF-1.7\nsynthetic test content",
    )

    with patch(
        "app.services.resume_service.extract_resume_text",
        return_value="Python developer with API experience",
    ) as parser:
        result = read_resume(file)

    assert "Python developer" in result
    parser.assert_called_once()


def test_accept_valid_docx_content():
    file = make_upload(
        "resume.docx",
        make_docx_bytes(),
    )

    with patch(
        "app.services.resume_service.extract_resume_text",
        return_value="Software engineer with Python experience",
    ) as parser:
        result = read_resume(file)

    assert "Software engineer" in result
    parser.assert_called_once()


def test_reject_resume_without_readable_text():
    file = make_upload(
        "resume.pdf",
        b"%PDF-1.7\nsynthetic test content",
    )

    with patch(
        "app.services.resume_service.extract_resume_text",
        return_value="   ",
    ):
        with pytest.raises(HTTPException) as error:
            read_resume(file)

    assert error.value.status_code == 422

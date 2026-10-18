
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# --------------------------------------------------
# Resume Upload API Tests
# --------------------------------------------------

def test_upload_resume_success():
    with patch(
        "app.api.routes.resumes.read_resume",
        return_value="Python developer with FastAPI experience",
    ) as parser_mock:

        response = client.post(
            "/upload-resume",
            files={
                "file": (
                    "resume.pdf",
                    b"%PDF-1.7\nSynthetic resume",
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    assert response.json()["filename"] == "resume.pdf"
    assert (
        response.json()["extracted_text"]
        == "Python developer with FastAPI experience"
    )
    parser_mock.assert_called_once()


@pytest.mark.parametrize(
    "filename",
    ["resume.txt", "resume.exe", "resume.doc"],
)
def test_upload_resume_rejects_invalid_extension(filename):
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                filename,
                b"Invalid file",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400


def test_upload_resume_rejects_missing_file():
    response = client.post("/upload-resume")

    assert response.status_code == 422


def test_upload_resume_propagates_validation_error():
    with patch(
        "app.api.routes.resumes.read_resume",
        side_effect=HTTPException(
            status_code=413,
            detail="Resume exceeds the maximum allowed size.",
        ),
    ):
        response = client.post(
            "/upload-resume",
            files={
                "file": (
                    "resume.pdf",
                    b"%PDF-1.7\nSynthetic resume",
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 413


def test_upload_resume_handles_unexpected_error():
    with patch(
        "app.api.routes.resumes.read_resume",
        side_effect=RuntimeError("Synthetic parser failure"),
    ):
        response = client.post(
            "/upload-resume",
            files={
                "file": (
                    "resume.pdf",
                    b"%PDF-1.7\nSynthetic resume",
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 500
    assert "Resume extraction failed" in response.json()["detail"]


# --------------------------------------------------
# Job Description API Tests
# --------------------------------------------------

def test_job_description_success():
    response = client.post(
        "/job-description",
        json={
            "job_title": "Python Developer",
            "job_description": (
                "Develop APIs using Python and FastAPI."
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["job_title"] == "Python Developer"
    assert body["job_description"] == (
        "Develop APIs using Python and FastAPI."
    )


def test_job_description_trims_whitespace():
    response = client.post(
        "/job-description",
        json={
            "job_title": "  Python Developer  ",
            "job_description": "  Develop Python APIs.  ",
        },
    )

    assert response.status_code == 200
    assert response.json()["job_title"] == "Python Developer"
    assert response.json()["job_description"] == "Develop Python APIs."


@pytest.mark.parametrize(
    "job_title, job_description",
    [
        ("", "Develop Python APIs."),
        ("Python Developer", ""),
        ("   ", "Develop Python APIs."),
        ("Python Developer", "   "),
    ],
)
def test_job_description_rejects_empty_fields(
    job_title,
    job_description,
):
    response = client.post(
        "/job-description",
        json={
            "job_title": job_title,
            "job_description": job_description,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"job_title": "Python Developer"},
        {"job_description": "Develop Python APIs."},
        {},
    ],
)
def test_job_description_rejects_missing_fields(payload):
    response = client.post(
        "/job-description",
        json=payload,
    )

    assert response.status_code == 422


def test_job_description_rejects_invalid_data_type():
    response = client.post(
        "/job-description",
        json={
            "job_title": ["Python", "Developer"],
            "job_description": "Develop Python APIs.",
        },
    )

    assert response.status_code == 422

from unittest.mock import MagicMock, patch

import pytest

from app.integrations.job_discovery.resume_profiler import (
    ResumeProfileExtraction,
    profile_from_resume,
    profile_from_text,
)


@patch("app.integrations.job_discovery.resume_profiler.create_chat_model")
def test_resume_profile_extraction(mock_create_model):
    structured_model = MagicMock()

    structured_model.invoke.return_value = ResumeProfileExtraction(
        target_titles=["Senior Python Developer", "Backend Engineer"],
        skills=["Python", "FastAPI", "AWS"],
        experience_years=5,
    )

    mock_create_model.return_value.with_structured_output.return_value = (
        structured_model
    )

    profile = profile_from_text(
        resume_text="Python developer with five years of experience.",
        location="Houston",
    )

    assert profile.target_titles == [
        "Senior Python Developer",
        "Backend Engineer",
    ]
    assert "Python" in profile.skills
    assert profile.experience_years == 5
    assert profile.location == "Houston"
    assert profile.remote_only is False


def test_empty_resume_text():
    with pytest.raises(ValueError, match="cannot be empty"):
        profile_from_text("   ")


@patch("app.integrations.job_discovery.resume_profiler.profile_from_text")
@patch("app.integrations.job_discovery.resume_profiler.load_resume")
def test_resume_file_uses_existing_loader(mock_loader, mock_profile):
    mock_loader.return_value = "Synthetic resume text"

    profile_from_resume(
        filename="test_resume.pdf",
        file_bytes=b"synthetic bytes",
        location="Houston",
        remote_only=True,
    )

    mock_loader.assert_called_once_with(
        "test_resume.pdf",
        b"synthetic bytes",
    )

    mock_profile.assert_called_once_with(
        resume_text="Synthetic resume text",
        location="Houston",
        remote_only=True,
    )

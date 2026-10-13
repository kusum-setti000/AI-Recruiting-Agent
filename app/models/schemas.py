from typing import Literal
from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    job_title: str
    job_description: str


class JobAlignment(BaseModel):
    status: Literal["aligned", "conflict", "unclear"]
    reason: str


class CandidateAnalysis(BaseModel):
    match_score: int = Field(ge=0, le=100)

    matching_skills: list[str]
    missing_skills: list[str]
    candidate_strengths: list[str]

    experience_alignment: str
    potential_gaps: list[str]
    recruiter_questions: list[str]

    overall_assessment: Literal[
        "Strong Match",
        "Potential Match",
        "Needs Human Review",
        "Weak Match",
    ]

    assessment_reasoning: str
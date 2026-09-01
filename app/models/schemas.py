from pydantic import BaseModel


class JobDescription(BaseModel):
    job_title: str
    job_description: str

class CandidateAnalysis(BaseModel):
    match_score: int
    matching_skills: list[str]
    missing_skills: list[str]
    candidate_strengths: list[str]
    experience_alignment: str
    potential_gaps: list[str]
    recruiter_questions: list[str]
    overall_assessment: str
    assessment_reasoning: str
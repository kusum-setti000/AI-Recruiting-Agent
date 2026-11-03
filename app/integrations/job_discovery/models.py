from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class CandidateJobProfile(BaseModel):
    target_titles: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    location: Optional[str] = None
    remote_only: bool = False
    experience_years: Optional[float] = Field(default=None, ge=0)


class MatchExplanation(BaseModel):
    matched_skills: list[str] = Field(default_factory=list)
    unmatched_candidate_skills: list[str] = Field(default_factory=list)
    title_similarity: float = Field(ge=0, le=1)
    candidate_experience_years: Optional[float] = None
    required_experience_years: Optional[float] = None
    experience_gap_years: float = Field(default=0, ge=0)
    experience_penalty_points: int = Field(default=0, ge=0)


class DiscoveredJob(BaseModel):
    source: str
    external_id: str
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    job_url: HttpUrl
    match_score: Optional[int] = Field(default=None, ge=0, le=100)
    match_explanation: Optional[MatchExplanation] = None
    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class JobDiscoveryResult(BaseModel):
    jobs: list[DiscoveredJob] = Field(default_factory=list)
    total_found: int = Field(default=0, ge=0)
    new_jobs: int = Field(default=0, ge=0)

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class CandidateJobProfile(BaseModel):
    target_titles: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    location: Optional[str] = None
    remote_only: bool = False
    experience_years: Optional[float] = Field(default=None, ge=0)


class DiscoveredJob(BaseModel):
    source: str
    external_id: str
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    job_url: HttpUrl
    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class JobDiscoveryResult(BaseModel):
    jobs: list[DiscoveredJob] = Field(default_factory=list)
    total_found: int = Field(default=0, ge=0)
    new_jobs: int = Field(default=0, ge=0)

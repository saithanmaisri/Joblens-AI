"""Request and response schemas. These also validate untrusted API input."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ApplicationStatus = Literal["Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected"]


class ProfileUpdate(BaseModel):
    resume_text: str = Field(min_length=1, max_length=100_000)


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    resume_text: str
    source_filename: str | None = None
    updated_at: datetime | None = None


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(default="Not specified", max_length=200)
    location: str = Field(default="Not specified", max_length=200)
    description: str = Field(min_length=1, max_length=50_000)
    required_skills: list[str] = Field(default_factory=list, max_length=100)
    job_url: str | None = Field(default=None, max_length=1000)

    @field_validator("required_skills")
    @classmethod
    def trim_skills(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(v.strip() for v in values if v.strip()))


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    company: str
    location: str
    description: str
    required_skills: list[str]
    job_url: str | None
    created_at: datetime


class AnalyzeRequest(BaseModel):
    resume_text: str | None = Field(default=None, max_length=100_000)
    job_title: str = Field(default="Target role", max_length=200)
    job_description: str = Field(min_length=1, max_length=50_000)
    required_skills: list[str] = Field(default_factory=list, max_length=100)


class AnalyzeResponse(BaseModel):
    job_title: str
    match_score: float
    skill_coverage_score: float
    text_similarity_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    profile_skills: list[str]
    job_skills: list[str]
    recommendations: list[str]
    scoring_note: str


class ApplicationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    status: ApplicationStatus = "Saved"
    job_url: str | None = Field(default=None, max_length=1000)
    notes: str = Field(default="", max_length=10_000)


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = Field(default=None, max_length=10_000)


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    company: str
    status: str
    job_url: str | None
    notes: str
    created_at: datetime
    updated_at: datetime


class AnalyticsOut(BaseModel):
    total_jobs: int
    total_applications: int
    status_counts: dict[str, int]

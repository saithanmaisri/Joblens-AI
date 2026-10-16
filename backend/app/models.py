"""Persistent database models."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    # A single editable profile is enough for this personal-project MVP.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    resume_text: Mapped[str] = mapped_column(Text, default="")
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    company: Mapped[str] = mapped_column(String(200), default="Not specified")
    location: Mapped[str] = mapped_column(String(200), default="Not specified")
    description: Mapped[str] = mapped_column(Text)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    job_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    company: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(40), default="Saved", index=True)
    job_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

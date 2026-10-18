"""JobLens AI: career matching and application-tracking API."""
from io import BytesIO
import os

import pdfplumber
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .matcher import calculate_match
from .models import Application, CandidateProfile, Job, User
from .auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from .schemas import (
    AnalyzeRequest, AnalyzeResponse, AnalyticsOut,
    ApplicationCreate, ApplicationOut, ApplicationUpdate,
    AuthResponse, JobCreate, JobOut, LoginRequest,
    ProfileOut, ProfileUpdate, SignupRequest, UserOut,
)

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Return the logged-in user from a valid bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in to continue.",
        )

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired login token. Please log in again.",
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found. Please log in again.",
        )

    return user

Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="JobLens AI API",
    description="Explainable role matching, resume text extraction, and job-application tracking.",
    version="1.0.0",
)
origins = [origin.strip() for origin in os.getenv(
    "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "JobLens AI API is running", "docs": "/docs"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "joblens-ai"}


@app.post("/api/auth/signup", response_model=AuthResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    name = payload.name.strip()
    email = payload.email.strip().lower()

    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Name must contain at least 2 characters.")

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )
    if existing_user:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not create your account.")

    token = create_access_token(user.id)
    return AuthResponse(
        access_token=token,
        user=UserOut(id=user.id, name=user.name, email=user.email),
    )


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
        )

    token = create_access_token(user.id)
    return AuthResponse(
        access_token=token,
        user=UserOut(id=user.id, name=user.name, email=user.email),
    )


@app.get("/api/profile", response_model=ProfileOut | None)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalar(
        select(CandidateProfile).where(
            CandidateProfile.user_id == current_user.id
        )
    )


@app.put("/api/profile", response_model=ProfileOut)
def save_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.scalar(
        select(CandidateProfile).where(
            CandidateProfile.user_id == current_user.id
        )
    )

    if profile is None:
        profile = CandidateProfile(
            user_id=current_user.id,
            resume_text=payload.resume_text,
        )
        db.add(profile)
    else:
        profile.resume_text = payload.resume_text
        profile.source_filename = None

    db.commit()
    db.refresh(profile)
    return profile


@app.post("/api/profile/upload", response_model=ProfileOut)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type != "application/pdf" and not (
        (file.filename or "").lower().endswith(".pdf")
    ):
        raise HTTPException(status_code=400, detail="Upload a PDF file.")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF must be 5 MB or smaller.")

    try:
        with pdfplumber.open(BytesIO(content)) as pdf:
            text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            ).strip()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read this PDF. Try exporting it as a text-based PDF.",
        ) from exc

    if not text:
        raise HTTPException(
            status_code=422,
            detail="No selectable text found. Scanned PDFs need OCR, which this version does not include.",
        )

    profile = db.scalar(
        select(CandidateProfile).where(
            CandidateProfile.user_id == current_user.id
        )
    )

    if profile is None:
        profile = CandidateProfile(
            user_id=current_user.id,
            resume_text=text,
            source_filename=file.filename,
        )
        db.add(profile)
    else:
        profile.resume_text = text
        profile.source_filename = file.filename

    db.commit()
    db.refresh(profile)
    return profile

@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume_text = payload.resume_text
    if not resume_text.strip():
        profile = db.scalar(
            select(CandidateProfile).where(
                CandidateProfile.user_id == current_user.id
            )
        )
        resume_text = profile.resume_text if profile else ""
    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Save or upload your resume/profile before analyzing a job.",
        )
    return calculate_match(
        resume_text,
        payload.job_title,
        payload.job_description,
        payload.required_skills,
    )


@app.get("/api/jobs", response_model=list[JobOut])
def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Job)
        .where(Job.user_id == current_user.id)
        .order_by(Job.created_at.desc())
    ).all()


@app.post("/api/jobs", response_model=JobOut, status_code=201)
def create_job(
    payload: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = Job(**payload.model_dump(), user_id=current_user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.delete("/api/jobs/{job_id}")
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.user_id == current_user.id,
        )
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Saved job not found.")

    db.delete(job)
    db.commit()
    return {"deleted": True, "id": job_id}

@app.get("/api/applications", response_model=list[ApplicationOut])
def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Application)
        .where(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
    ).all()


@app.post("/api/applications", response_model=ApplicationOut, status_code=201)
def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = Application(
        **payload.model_dump(),
        user_id=current_user.id,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.patch("/api/applications/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = db.scalar(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, key, value)

    db.commit()
    db.refresh(application)
    return application


@app.delete("/api/applications/{application_id}")
def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = db.scalar(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")

    db.delete(application)
    db.commit()
    return {"deleted": True, "id": application_id}

@app.get("/api/analytics", response_model=AnalyticsOut)
def analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total_jobs = db.scalar(
        select(func.count())
        .select_from(Job)
        .where(Job.user_id == current_user.id)
    ) or 0
    total_applications = db.scalar(
        select(func.count())
        .select_from(Application)
        .where(Application.user_id == current_user.id)
    ) or 0
    rows = db.execute(
        select(Application.status, func.count())
        .where(Application.user_id == current_user.id)
        .group_by(Application.status)
    ).all()
    counts = {status: count for status, count in rows}
    for status in ("Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected"):
        counts.setdefault(status, 0)
    return {
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "status_counts": counts,
    }

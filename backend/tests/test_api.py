"""Small API regression suite; run with: pytest -q"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_identifies_missing_skills(client):
    save = client.put("/api/profile", json={"resume_text": "I use Python, SQL, pandas and Power BI for reporting."})
    assert save.status_code == 200
    response = client.post("/api/analyze", json={
        "job_title": "Data Analyst",
        "job_description": "Build dashboards and automate reporting with Python, SQL, Power BI, and Tableau.",
        "required_skills": ["Python", "SQL", "Power BI", "Tableau"],
    })
    assert response.status_code == 200
    result = response.json()
    assert set(result["matched_skills"]) == {"Python", "SQL", "Power BI"}
    assert result["missing_skills"] == ["Tableau"]
    assert 0 <= result["match_score"] <= 100


def test_create_job_and_application_analytics(client):
    job = client.post("/api/jobs", json={
        "title": "Python Intern", "company": "Example Co", "location": "Hyderabad",
        "description": "Python and SQL development", "required_skills": ["Python", "SQL"]
    })
    assert job.status_code == 201
    application = client.post("/api/applications", json={
        "title": "Python Intern", "company": "Example Co", "status": "Applied"
    })
    assert application.status_code == 201
    stats = client.get("/api/analytics").json()
    assert stats["total_jobs"] == 1
    assert stats["total_applications"] == 1
    assert stats["status_counts"]["Applied"] == 1


def test_invalid_application_status_is_rejected(client):
    response = client.post("/api/applications", json={
        "title": "Intern", "company": "Example Co", "status": "Maybe"
    })
    assert response.status_code == 422

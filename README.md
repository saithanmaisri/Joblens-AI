# JobLens AI — Career Intelligence Workspace

JobLens AI is an advanced learning project combining a React dashboard, FastAPI, SQL persistence, PDF text extraction, NLP-style text matching, and job-search analytics.

## What works in this MVP

- Save resume text or upload a text-based PDF (maximum 5 MB).
- Detect skills from a small, editable vocabulary.
- Compare a profile against a role using transparent skill coverage and TF-IDF text similarity.
- Save and remove job descriptions.
- Track applications and update their pipeline stage.
- See basic application analytics.
- Validate API behavior with automated tests.

> **Important:** the match score is a heuristic for learning and prioritizing practice. It is not a hiring probability, an assessment of a person's worth, or a substitute for a recruiter. TF-IDF measures text overlap; it is not a modern semantic embedding model. PDF OCR, authentication, multi-user support, and production-grade security are not included yet.

## Architecture

```text
React + Vite (port 5173)
       | HTTP / JSON + multipart PDF upload
       v
FastAPI (port 8000) ---- scikit-learn (TF-IDF + cosine similarity)
       |
       v
SQLAlchemy ORM ---- SQLite (local file: backend/joblens.db)
                    PostgreSQL via DATABASE_URL in deployment
```

## Prerequisites

- Python 3.11 or 3.12 recommended.
- Node.js 22.12+ recommended for the current Vite toolchain; Vite's current guide lists Node.js 20.19+ or 22.12+ as supported minimums: https://vite.dev/guide/.
- Git (optional, for version control).

Confirm versions:

```bash
python --version
node --version
npm --version
```

## 1. Start the backend (Windows PowerShell)

Open a terminal in the project folder:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell blocks environment activation, use Command Prompt and run:

```bat
.venv\Scripts\activate.bat
```

Linux/macOS equivalent:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/api/health` and open interactive API docs at `http://127.0.0.1:8000/docs`.

## 2. Start the frontend

Use a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). Keep both terminals running during development.

If the backend runs somewhere other than `http://127.0.0.1:8000`, create `frontend/.env.local`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Restart Vite after changing environment variables.

## 3. Test the backend

From the backend folder with the virtual environment active:

```bash
pytest -q
```

Expected result: four tests pass. If a package installation fails, record the complete error and Python/Node versions before changing dependency versions.

## 4. Suggested manual test path

1. Open JobLens AI and paste resume text into the profile area; click **Save profile**.
2. Paste a real job description into the role matcher. Keep the skills list comma-separated and correct any vocabulary misses.
3. Click **Analyze role**. Compare detected/missing skills and read the scoring caveat.
4. Click **Save job**, verify the job appears in Job Library, then delete it to exercise the DELETE endpoint.
5. Add an application, change its stage in the table, and verify that the metrics update.
6. Upload a normal text-based PDF. A scanned/image-only PDF is not supported yet because OCR is not included.

## 5. API map

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET / PUT | `/api/profile` | Read or save resume text |
| POST | `/api/profile/upload` | Extract text from PDF |
| POST | `/api/analyze` | Generate role-match report |
| GET / POST | `/api/jobs` | List or save jobs |
| DELETE | `/api/jobs/{id}` | Delete saved job |
| GET / POST | `/api/applications` | List or track applications |
| PATCH / DELETE | `/api/applications/{id}` | Update stage/notes or delete |
| GET | `/api/analytics` | Pipeline counts |

## 6. GitHub

From the project root:

```bash
git init
git add .
git commit -m "Build JobLens AI career intelligence MVP"
```

Create an empty repository on GitHub, then follow GitHub's displayed instructions to add its remote and push. Do not commit real personal resumes, database files, credentials, or `.env` files. Keep demo resume text fictional or anonymized.

## 7. Deployment roadmap

Recommended split deployment:

- **Frontend:** Vercel; set `VITE_API_BASE_URL` to the deployed API URL.
- **Backend:** Render or another Python ASGI host; start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Database:** use managed PostgreSQL for persistent production data and set `DATABASE_URL` on the backend. Set `FRONTEND_ORIGINS` to the exact deployed frontend origin.

The local SQLite database is appropriate for learning. Some hosts use ephemeral filesystems, so do not assume a SQLite file will persist after redeployment. Before using real personal data, add authentication, ownership checks, rate limits, secret management, retention/deletion controls, and HTTPS. Do not make this unauthenticated MVP public with sensitive resumes.

## Learning milestones after the MVP

1. **Engineering quality:** add Alembic migrations, structured logging, service/repository layers, and stronger tests.
2. **More useful NLP:** compare TF-IDF with sentence-transformer embeddings; evaluate both approaches on a small labeled test set before claiming it is better.
3. **Data analytics:** add SQL views and charts for application conversion, response rates, and time in each stage.
4. **Full-stack quality:** add authentication, pagination, filtering, form validation, and accessibility checks.
5. **Deployment:** managed PostgreSQL + hosted FastAPI + Vercel, CI tests in GitHub Actions, and monitoring.

# JobLens AI — AI-Powered Career Intelligence Platform

**Analyze your resume. Understand your job fit. Organize your job search.**

JobLens AI is a full-stack web application that helps job seekers analyze resumes against job descriptions, identify relevant skills, evaluate job compatibility, organize opportunities, and track application progress in one place.

The platform combines a React frontend, FastAPI backend, PostgreSQL database, PDF text extraction, and explainable text-matching techniques.

<p align="center">

  **[Live Application](https://joblens-ai-sage.vercel.app) · [GitHub Repository](https://github.com/saithanmaisri/Joblens-AI) · [API Documentation](https://joblens-ai-backend.onrender.com/docs)**

</p>

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [How Job Matching Works](#how-job-matching-works)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Overview](#api-overview)
- [Deployment](#deployment)
- [Security](#security)
- [Limitations](#limitations)
- [Future Enhancements](#future-enhancements)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview

Job searching often involves repeatedly comparing resumes with job descriptions, identifying missing skills, saving opportunities, and tracking applications across different platforms.

JobLens AI brings these activities together in a centralized workspace.

Users can maintain their resume profile, analyze compatibility with target roles, review matching insights, save job opportunities, manage application statuses, and view job-search analytics.

The project demonstrates the integration of full-stack web development, REST API design, database persistence, authentication, PDF processing, and natural language text analysis.

## Key Features

### 1. User Authentication
- User registration and login.
- Password hashing for secure password storage.
- JWT-based authentication for protected API requests.
- Authenticated access to user-specific resources.

### 2. Resume Management
- Save and update resume text.
- Upload supported PDF resumes.
- Extract text from text-based PDF documents.
- Reuse saved resume information during job analysis.

### 3. Resume-to-Job Matching
- Compare resume content with a job description.
- Evaluate text similarity using TF-IDF and cosine similarity.
- Identify matching skills and potential skill gaps.
- Display compatibility insights to support job-search decisions.

### 4. Job Library
- Save job opportunities for future reference.
- Organize job details in one place.
- Retrieve and remove saved job records.

### 5. Application Tracker
- Maintain job application records.
- Track application stages and progress.
- Update application information.
- Keep job-search activities organized.

### 6. Dashboard Analytics
- View summaries of saved jobs and application activity.
- Review application pipeline information.
- Use stored application data to monitor job-search progress.

### 7. Persistent Data Storage
- Store application data in PostgreSQL.
- Use SQLAlchemy for database interactions.
- Associate records with authenticated users.
- Enforce user-specific access to protected resources.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, JavaScript, Vite |
| Backend | Python, FastAPI |
| API | REST APIs, JSON |
| Database | PostgreSQL |
| Database hosting | Neon |
| ORM | SQLAlchemy |
| Authentication | JWT, password hashing |
| PDF processing | pdfplumber |
| Text analysis | Scikit-learn, TF-IDF, cosine similarity |
| Frontend deployment | Vercel |
| Backend deployment | Render |
| Version control | Git, GitHub |

---

## System Architecture

```text
                 User
                  |
                  v
       React + Vite Frontend
               Vercel
                  |
            HTTPS / REST
                  |
                  v
          FastAPI Backend
               Render
                  |
        +---------+----------+
        |         |          |
        v         v          v
   Authentication Resume   Job Matching
                  Processing   Engine
        |         |          |
        +---------+----------+
                  |
                  v
             SQLAlchemy
                  |
                  v
          Neon PostgreSQL
```

### Request Flow

1. The user interacts with the React frontend.
2. The frontend sends HTTP requests to the FastAPI backend.
3. The backend validates requests and authenticates protected operations.
4. Application logic processes resume analysis, job matching, or tracking operations.
5. SQLAlchemy communicates with PostgreSQL.
6. The backend returns JSON responses to the frontend.

---

## How Job Matching Works

JobLens AI uses text-processing techniques to provide explainable resume-to-job comparisons.

### Step 1: Resume and job description input

The user provides resume text and a target job description.

### Step 2: Text processing

The matching engine prepares the text for comparison and evaluates relevant skills using the project's configured skill vocabulary.

### Step 3: TF-IDF representation

TF-IDF (Term Frequency–Inverse Document Frequency) converts text into numerical features based on the importance of words within the compared documents.

### Step 4: Cosine similarity

Cosine similarity measures the similarity between the resulting text vectors.

\[
\text{Cosine Similarity}(A,B)=
\frac{A\cdot B}{\|A\|\|B\|}
\]

### Step 5: Skill analysis

The application evaluates skills found in the resume against skills associated with the target role, helping identify strengths and potential gaps.

### Step 6: Results

The application presents the available matching metrics and skill insights to help users prioritize relevant opportunities and improve their resumes.

**Important:** Match scores are heuristic decision-support indicators. They are not hiring probabilities, guarantees of shortlisting, or substitutes for recruiter evaluation.

---

## Getting Started

### Prerequisites

Install the following tools:

- Python 3.11
- Node.js compatible with the installed Vite version
- npm
- Git
- A PostgreSQL database or a suitable local database configuration

Check your installed versions:

```bash
python --version
node --version
npm --version
git --version
```

### 1. Clone the repository

```bash
git clone https://github.com/saithanmaisri/Joblens-AI.git
cd Joblens-AI
```

### 2. Set up the backend

Open a terminal in the project root and run:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

### 3. Configure the backend

Create a `.env` file in the `backend` directory.

Example:

```env
DATABASE_URL=your_database_connection_string
SECRET_KEY=your_private_random_secret
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Replace the example values with your own configuration. Never commit real database credentials or secret keys.

### 4. Start the backend

From the `backend` directory, with the virtual environment activated:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check the API health endpoint:

[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

Open the interactive API documentation:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Keep the backend terminal running.

### 5. Set up the frontend

Open a second terminal from the project root:

```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend` directory:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 6. Start the frontend

```bash
npm run dev
```

Open the local URL printed by Vite, normally:

[http://localhost:5173](http://localhost:5173)

Keep both the frontend and backend running while using the local application.

If you change frontend environment variables, restart the Vite development server.

---

## Environment Variables

### Backend

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Database connection string |
| `SECRET_KEY` | Private signing key used by JWT authentication |
| `FRONTEND_ORIGINS` | Allowed frontend origins for CORS |

### Frontend

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend |

For local development, point `VITE_API_BASE_URL` to `http://127.0.0.1:8000`.

For production, configure it to use the deployed backend URL.

**Security note:** Variables prefixed with `VITE_` are exposed to frontend code. Never place database credentials, private API keys, or JWT signing secrets in frontend environment variables.

---

## API Overview

JobLens AI exposes REST API endpoints through FastAPI.

The deployed interactive documentation is available at:

**[Open JobLens AI Swagger UI](https://joblens-ai-backend.onrender.com/docs)**

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Basic API status |
| `GET` | `/api/health` | Health check |
| `POST` | `/api/auth/signup` | Register a user |
| `POST` | `/api/auth/login` | Authenticate a user |
| `GET` | `/api/profile` | Retrieve the authenticated user's profile |
| `POST` | `/api/profile/update` | Update profile information |
| `POST` | `/api/analyze` | Analyze resume and job compatibility |
| `GET` | `/api/jobs` | Retrieve saved jobs |
| `POST` | `/api/jobs` | Save a job |
| `GET` | `/api/applications` | Retrieve application records |
| `POST` | `/api/applications` | Create an application record |
| `GET` | `/api/analytics` | Retrieve dashboard analytics |

Additional job-management, application-update, deletion, and PDF-upload routes may be available in the deployed API. Check Swagger UI for the exact methods, request schemas, and route definitions in the current version.

Protected endpoints require a valid access token where specified by the API.

---

## Deployment

JobLens AI uses a split deployment architecture.

### Frontend — Vercel

Live application:

https://joblens-ai-sage.vercel.app

Configure the frontend environment variable:

```env
VITE_API_BASE_URL=https://joblens-ai-backend.onrender.com
```

### Backend — Render

Backend URL:

https://joblens-ai-backend.onrender.com

Typical service settings:

| Setting | Value |
|---|---|
| Root directory | `backend/` |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

Configure the backend environment variables in the Render service dashboard.

### Database — Neon

Neon PostgreSQL provides the hosted relational database.

Configure `DATABASE_URL` in the backend environment, using the connection string supplied by Neon. Do not expose the connection string publicly.

For deployment troubleshooting, verify database connectivity, CORS origins, environment variables, and backend logs.

---

## Security

The application includes important foundational security measures:

- Password hashing.
- JWT-based authentication.
- Authentication for protected API operations.
- User-specific resource access controls.
- Environment-based secret configuration.
- CORS configuration for approved frontend origins.
- HTTPS through the deployed hosting platforms.

Security is an ongoing responsibility. Before handling sensitive personal information at scale, review endpoint authorization, upload validation, dependency vulnerabilities, rate limiting, logging, data retention, and account/session management.

Never upload real user resumes, credentials, database files, or `.env` files to the public repository.

---

## Limitations

- Scanned or image-only PDFs require OCR, which is not included in the current text-extraction workflow.
- TF-IDF measures text overlap and does not provide the contextual understanding of modern semantic embedding models.
- Match scores depend on the supplied resume, job description, and configured skill-matching logic.
- Results do not guarantee hiring outcomes.
- The application does not automatically submit job applications to employers.
- Hosting providers may impose usage, availability, or resource limits.

---

## Future Enhancements

Potential future improvements include:

- OCR support for scanned resumes.
- Semantic matching with sentence embeddings.
- More detailed missing-skill and resume-improvement recommendations.
- Downloadable job-match reports.
- Improved dashboard visualizations.
- Application reminders and notifications.
- Additional automated integration and end-to-end tests.
- Better session renewal and account-management workflows.
- Accessibility and performance improvements.
- Optional job-board integrations where permitted.

These items represent possible enhancements and are not claims that they are already implemented.

---

## Project Structure

```text
Joblens-AI/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── matcher.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
├── .gitignore
└── README.md
```

This is a simplified overview. Additional files and modules may be present in the repository.

---

## Contributing

Contributions and suggestions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make and test your changes.
4. Commit your work with a descriptive message.
5. Open a pull request describing the changes.

Please avoid committing secrets, private resumes, generated database files, or personal information.

---

## License

No license is specified here. If you intend to distribute the project for reuse or modification, add an appropriate `LICENSE` file to the repository.

---

**Built with React, FastAPI, Python, PostgreSQL, and Scikit-learn.**

**Live Demo:** https://joblens-ai-sage.vercel.app  
**Source Code:** https://github.com/saithanmaisri/Joblens-AI  
**API Documentation:** https://joblens-ai-backend.onrender.com/docs


"""Explainable baseline job matcher built from keyword extraction + TF-IDF.

This is a learning/demo score, not a prediction of hiring or employability.
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "SQL": ("sql",),
    "MySQL": ("mysql",),
    "PostgreSQL": ("postgresql", "postgres"),
    "Excel": ("excel", "microsoft excel", "spreadsheets"),
    "Power BI": ("power bi", "powerbi"),
    "Tableau": ("tableau",),
    "Pandas": ("pandas",),
    "NumPy": ("numpy",),
    "Scikit-learn": ("scikit-learn", "scikit learn", "sklearn"),
    "Machine Learning": ("machine learning",),
    "NLP": ("natural language processing", "nlp"),
    "Generative AI": (
        "generative ai", "genai", "large language model",
        "large language models", "llm", "llms",
    ),
    "FastAPI": ("fastapi",),
    "Django": ("django",),
    "React": ("react.js", "react"),
    "JavaScript": ("javascript",),
    "HTML/CSS": ("html", "css", "html/css"),
    "Git": ("git",),
    "GitHub": ("github",),
    "REST APIs": (
        "rest api", "rest apis", "restful api", "restful apis",
        "restful services",
    ),
    "Docker": ("docker",),
    "AWS": ("aws", "amazon web services"),
    "Testing": ("testing", "pytest", "unit testing", "automated testing"),
    "Statistics": ("statistics", "statistical analysis"),
    "Data Analysis": (
        "data analysis", "data analytics", "data analyst",
        "data analyses", "analyzing data", "analysing data",
    ),
    "Data Visualization": (
        "data visualization", "data visualisation",
        "matplotlib", "seaborn",
    ),
    "MongoDB": ("mongodb",),
    "TensorFlow": ("tensorflow",),
    "PyTorch": ("pytorch",),
    "Communication": ("communication", "stakeholder communication"),
    "Agile": ("agile", "scrum"),
    "Problem Solving": (
        "problem solving", "problem-solving", "analytical thinking",
    ),
}


def _contains_phrase(text: str, phrase: str) -> bool:
    """Match a phrase without accidentally matching inside a longer word."""
    escaped = re.escape(phrase.lower()).replace(r"\ ", r"\s+")
    return (
        re.search(
            r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])",
            text.lower(),
        )
        is not None
    )


def extract_skills(text: str) -> list[str]:
    """Extract recognized skills from text."""
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(_contains_phrase(text, alias) for alias in aliases):
            found.append(canonical)
    return found


def normalize_required_skills(
    skills: list[str], job_text: str
) -> list[str]:
    """Normalize user-entered skill names; infer skills if none are supplied."""
    if not skills:
        return extract_skills(job_text)

    normalized = []
    alias_map = {
        alias.lower(): name
        for name, aliases in SKILL_ALIASES.items()
        for alias in aliases
    }
    canonical_map = {name.lower(): name for name in SKILL_ALIASES}

    for requested in skills:
        key = requested.strip().lower()
        if not key:
            continue

        canonical = canonical_map.get(key, alias_map.get(key, requested.strip()))
        if canonical not in normalized:
            normalized.append(canonical)

    return normalized


def calculate_match(
    resume_text: str,
    job_title: str,
    job_description: str,
    required_skills: list[str] | None = None,
) -> dict:
    profile_skills = extract_skills(resume_text)
    job_text = f"{job_title}\n{job_description}"
    job_skills = normalize_required_skills(
        required_skills or [], job_text
    )

    matched = [skill for skill in job_skills if skill in profile_skills]
    missing = [skill for skill in job_skills if skill not in profile_skills]

    coverage = (
        len(matched) / len(job_skills) * 100
        if job_skills else 0.0
    )

    text_similarity = 0.0
    if resume_text.strip() and job_text.strip():
        try:
            matrix = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_features=6000,
            ).fit_transform([resume_text, job_text])
            text_similarity = float(
                cosine_similarity(matrix[0:1], matrix[1:2])[0, 0] * 100
            )
        except ValueError:
            text_similarity = 0.0

    if job_skills:
        overall = 0.70 * coverage + 0.30 * text_similarity
        scoring_note = (
            "Heuristic score from skill overlap (70%) and TF-IDF text "
            "similarity (30%); not a probability of getting hired."
        )
    else:
        overall = text_similarity
        scoring_note = (
            "No recognized job skills were detected. The score uses TF-IDF "
            "text similarity only; it is not a probability of getting hired."
        )

    recommendations = []
    if missing:
        recommendations.append(
            "Prioritize building evidence for: "
            + ", ".join(missing[:8]) + "."
        )
    if text_similarity < 15:
        recommendations.append(
            "Tailor your profile with truthful, specific examples "
            "that use the role's terminology."
        )
    if not job_skills:
        recommendations.append(
            "No skills from the built-in vocabulary were detected; "
            "add required skills manually for a better analysis."
        )
    if not recommendations:
        recommendations.append(
            "Good initial alignment. Prepare one concrete project "
            "or work example for each matched skill."
        )

    return {
        "job_title": job_title,
        "match_score": round(max(0.0, min(100.0, overall)), 1),
        "skill_coverage_score": round(coverage, 1),
        "text_similarity_score": round(text_similarity, 1),
        "matched_skills": matched,
        "missing_skills": missing,
        "profile_skills": profile_skills,
        "job_skills": job_skills,
        "recommendations": recommendations,
        "scoring_note": scoring_note,
    }

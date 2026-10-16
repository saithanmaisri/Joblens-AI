"""Explainable baseline job matcher built from keyword extraction + TF-IDF.

This is a learning/demo score, not a prediction of hiring or employability.
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Add aliases here as you learn how job descriptions phrase the same skills.
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
    "Generative AI": ("generative ai", "genai", "large language model", "llm", "llms"),
    "FastAPI": ("fastapi",),
    "Django": ("django",),
    "React": ("react.js", "react",),
    "JavaScript": ("javascript",),
    "HTML/CSS": ("html", "css"),
    "Git": ("git", "github"),
    "REST APIs": ("rest api", "rest apis", "restful api", "restful apis"),
    "Docker": ("docker",),
    "AWS": ("aws", "amazon web services"),
    "Testing": ("testing", "pytest", "unit testing",),
    "Statistics": ("statistics", "statistical analysis"),
    "Data Visualization": ("data visualization", "matplotlib", "seaborn"),
    "MongoDB": ("mongodb",),
    "TensorFlow": ("tensorflow",),
    "PyTorch": ("pytorch",),
    "Communication": ("communication", "stakeholder communication"),
    "Agile": ("agile", "scrum"),
    "Problem Solving": ("problem solving", "analytical thinking"),
}


def _contains_phrase(text: str, phrase: str) -> bool:
    # Boundaries avoid accidental matches such as "sql" inside a longer word.
    escaped = re.escape(phrase.lower()).replace(r"\ ", r"\s+")
    return re.search(r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])", text.lower()) is not None


def extract_skills(text: str) -> list[str]:
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(_contains_phrase(text, alias) for alias in aliases):
            found.append(canonical)
    return found


def normalize_required_skills(skills: list[str], job_text: str) -> list[str]:
    """Map user-entered skill names to canonical labels; infer from text if omitted."""
    if not skills:
        return extract_skills(job_text)
    normalized = []
    for requested in skills:
        key = requested.strip().lower()
        if not key:
            continue
        canonical = next(
            (name for name, aliases in SKILL_ALIASES.items()
             if key == name.lower() or key in {alias.lower() for alias in aliases}),
            requested.strip(),
        )
        if canonical not in normalized:
            normalized.append(canonical)
    return normalized


def calculate_match(resume_text: str, job_title: str, job_description: str,
                    required_skills: list[str] | None = None) -> dict:
    profile_skills = extract_skills(resume_text)
    job_skills = normalize_required_skills(required_skills or [], f"{job_title}\n{job_description}")
    matched = [skill for skill in job_skills if skill in profile_skills]
    missing = [skill for skill in job_skills if skill not in profile_skills]
    coverage = (len(matched) / len(job_skills) * 100) if job_skills else 0.0

    text_similarity = 0.0
    if resume_text.strip() and job_description.strip():
        try:
            matrix = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=6000).fit_transform(
                [resume_text, f"{job_title}\n{job_description}"]
            )
            text_similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0, 0] * 100)
        except ValueError:
            # For example, both texts may contain only stop words or punctuation.
            text_similarity = 0.0

    # When job skills can be identified, weight transparent skill coverage more heavily.
    # Otherwise use text overlap only and make the lack of detected skills explicit.
    overall = 0.70 * coverage + 0.30 * text_similarity if job_skills else text_similarity
    recommendations = []
    if missing:
        recommendations.append("Prioritize building evidence for: " + ", ".join(missing[:8]) + ".")
    if text_similarity < 15:
        recommendations.append("Tailor your profile with truthful, specific examples that use the role's terminology.")
    if not job_skills:
        recommendations.append("No skills from the built-in vocabulary were detected; add required skills manually for a better analysis.")
    if not recommendations:
        recommendations.append("Good initial alignment. Prepare one concrete project or work example for each matched skill.")

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
        "scoring_note": "Heuristic score from skill overlap (70%) and TF-IDF text similarity (30%); not a probability of getting hired.",
    }

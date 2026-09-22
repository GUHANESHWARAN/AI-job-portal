"""
AI Hybrid Matching Engine:
Calculates multi-dimensional compatibility between candidates and job listings
using skill graph overlap, TF-IDF semantic cosine similarity, and experience alignment.
Provides fully explainable matching breakdowns.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skill_extractor import calculate_skill_similarity


def calculate_semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Computes TF-IDF N-gram cosine similarity between two texts.
    Returns score as a float from 0.0 to 100.0.
    """
    if not text_a or not text_b or len(text_a.strip()) < 10 or len(text_b.strip()) < 10:
        return 50.0  # neutral fallback if text is sparse

    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            max_features=5000,
            sublinear_tf=True
        )
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
        cos_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        # Map raw cosine similarity to 0-100 scale using smooth power-law scaling
        score = min(100.0, float((cos_sim ** 0.6) * 100.0) if cos_sim > 0 else 0.0)
        return round(max(0.0, score), 1)
    except Exception as e:
        print(f"Error computing semantic similarity: {e}")
        return 50.0


def calculate_experience_alignment(
    job_exp_level: str,
    job_min_years: int,
    cand_grad_year: Optional[int] = None,
    cand_exp_years: int = 0
) -> float:
    """
    Evaluates how well candidate experience aligns with job seniority requirements.
    """
    level = (job_exp_level or 'entry').lower()

    if level in ('intern', 'entry') or job_min_years == 0:
        return 100.0 if cand_exp_years >= 0 else 90.0

    if cand_exp_years >= job_min_years:
        return 100.0
    elif cand_exp_years >= (job_min_years - 1):
        return 80.0
    elif cand_exp_years >= (job_min_years - 2):
        return 60.0
    else:
        return max(30.0, 100.0 - (job_min_years - cand_exp_years) * 20.0)


def compute_job_match(
    candidate_skills: List[str],
    resume_text: str,
    job_required_skills: List[str],
    job_preferred_skills: List[str],
    job_description: str,
    job_exp_level: str = 'entry',
    job_min_years: int = 0,
    cand_exp_years: int = 0
) -> Dict[str, Any]:
    """
    Computes overall composite match score and explainable breakdown.
    """
    # 1. Skill Match Score (45% weight)
    # Required skills (85% of skill score), Preferred skills (15% bonus)
    req_score, req_matched, req_missing = calculate_skill_similarity(candidate_skills, job_required_skills)
    pref_score, pref_matched, pref_missing = calculate_skill_similarity(candidate_skills, job_preferred_skills)

    if job_required_skills and job_preferred_skills:
        skill_score = (req_score * 0.85) + (pref_score * 0.15)
    elif job_required_skills:
        skill_score = req_score
    elif job_preferred_skills:
        skill_score = pref_score
    else:
        skill_score = 75.0  # neutral default

    # 2. Semantic Content Match Score (35% weight)
    semantic_score = calculate_semantic_similarity(resume_text, job_description)

    # 3. Experience Alignment Score (20% weight)
    exp_score = calculate_experience_alignment(job_exp_level, job_min_years, cand_exp_years=cand_exp_years)

    # Composite Overall Score (0 - 100)
    overall_score = (skill_score * 0.45) + (semantic_score * 0.35) + (exp_score * 0.20)
    overall_score = round(min(100.0, max(0.0, overall_score)), 1)

    # Determine match tier & verdict
    if overall_score >= 80.0:
        verdict = "High Match"
        verdict_badge = "success"
    elif overall_score >= 65.0:
        verdict = "Good Match"
        verdict_badge = "primary"
    elif overall_score >= 50.0:
        verdict = "Moderate Match"
        verdict_badge = "warning"
    else:
        verdict = "Low Match"
        verdict_badge = "danger"

    # Generate Strengths
    strengths = []
    if req_matched:
        strengths.append(f"Possesses core required skills: {', '.join(req_matched[:5])}")
    if pref_matched:
        strengths.append(f"Has bonus/preferred skills: {', '.join(pref_matched[:3])}")
    if semantic_score >= 70.0:
        strengths.append("High context relevance between project descriptions and job responsibilities")
    if exp_score >= 90.0:
        strengths.append("Experience level strictly satisfies position criteria")

    # Generate Weaknesses / Gaps
    weaknesses = []
    if req_missing:
        weaknesses.append(f"Missing mandatory requirements: {', '.join(req_missing[:4])}")
    if pref_missing:
        weaknesses.append(f"Lacks preferred technologies: {', '.join(pref_missing[:3])}")
    if semantic_score < 50.0:
        weaknesses.append("Resume contains low domain terminology overlap with the role description")

    # Summary Explanation
    if overall_score >= 80.0:
        summary_explanation = (
            f"Strong candidate profile for this position. The candidate matches {len(req_matched)} of "
            f"{len(job_required_skills or [1])} required skills with solid technical keyword alignment."
        )
    elif overall_score >= 65.0:
        summary_explanation = (
            f"Promising candidate with solid foundations. Possesses key competencies ({', '.join(req_matched[:3])}), "
            f"though upskilling in {', '.join(req_missing[:2]) or 'ancillary tools'} would strengthen fit."
        )
    elif overall_score >= 50.0:
        summary_explanation = (
            f"Moderate compatibility. Meets foundational criteria but exhibits gaps in key technical requirements "
            f"({', '.join(req_missing[:3])})."
        )
    else:
        summary_explanation = (
            f"Limited overlap for this specific role. Significant skill gaps identified in "
            f"{', '.join(req_missing[:4]) or 'core prerequisites'}."
        )

    return {
        'overall_score': overall_score,
        'skill_score': round(skill_score, 1),
        'semantic_score': round(semantic_score, 1),
        'experience_score': round(exp_score, 1),
        'verdict': verdict,
        'verdict_badge': verdict_badge,
        'matched_skills': req_matched + pref_matched,
        'matched_required': req_matched,
        'missing_required': req_missing,
        'matched_preferred': pref_matched,
        'missing_preferred': pref_missing,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'summary_explanation': summary_explanation
    }

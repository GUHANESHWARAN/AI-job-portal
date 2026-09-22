"""
Job Description (JD) Analyzer Engine:
Parses job descriptions, classifies required vs preferred skills,
determines experience requirements, and generates concise role summaries.
"""

import re
from typing import Any, Dict, List
from .skill_extractor import extract_skills, extract_categorized_skills


def extract_experience_requirements(text: str) -> Dict[str, Any]:
    """Extracts required years of experience and implied seniority level."""
    text_lower = text.lower()
    years = 0

    # Patterns like: "3+ years", "3-5 years", "minimum 4 years", "at least 2 years"
    range_match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)\s*\+?\s*years?', text_lower)
    if range_match:
        years = int(range_match.group(1))
    else:
        single_match = re.search(r'(\d+)\s*\+?\s*years?(?:\s+of\s+experience)?', text_lower)
        if single_match:
            years = int(single_match.group(1))

    # Determine seniority
    if 'lead' in text_lower or 'architect' in text_lower or 'principal' in text_lower or years >= 8:
        level = 'lead'
    elif 'senior' in text_lower or 'sr.' in text_lower or years >= 5:
        level = 'senior'
    elif 'mid' in text_lower or (2 <= years < 5):
        level = 'mid'
    elif 'intern' in text_lower or 'internship' in text_lower or 'trainee' in text_lower:
        level = 'intern'
    else:
        level = 'entry'

    return {
        'min_years': years,
        'level': level
    }


def extract_education_requirements(text: str) -> List[str]:
    """Identifies degree and academic background prerequisites."""
    edu_patterns = [
        (r"\b(bachelor'?s|b\.tech|b\.e\.|bs|b\.sc)\b", "Bachelor's Degree in Computer Science, IT, or related technical field"),
        (r"\b(master'?s|m\.tech|m\.e\.|ms|m\.sc)\b", "Master's Degree in CS, Data Science, or related field"),
        (r"\b(phd|ph\.d|doctorate)\b", "Ph.D. in Computer Science or specialized quantitative discipline"),
        (r"\b(diploma|associate)\b", "Associate Degree or Technical Diploma"),
    ]
    detected = []
    text_lower = text.lower()
    for pat, desc in edu_patterns:
        if re.search(pat, text_lower):
            detected.append(desc)
    return detected or ["Degree in Computer Science, Engineering, or relevant practical experience"]


def partition_skills_required_vs_preferred(text: str) -> Dict[str, List[str]]:
    """
    Separates detected skills into required (must-have) vs preferred (nice-to-have).
    """
    lines = text.split('\n')
    preferred_keywords = ['nice to have', 'good to have', 'preferred', 'plus', 'bonus', 'optional', 'advantage']
    required_keywords = ['required', 'must have', 'qualifications', 'prerequisites', 'essential', 'mandatory', 'requirements']

    current_mode = 'required'
    required_text = []
    preferred_text = []

    for line in lines:
        lower_line = line.lower()
        if any(kw in lower_line for kw in preferred_keywords):
            current_mode = 'preferred'
        elif any(kw in lower_line for kw in required_keywords):
            current_mode = 'required'

        if current_mode == 'preferred':
            preferred_text.append(line)
        else:
            required_text.append(line)

    req_skills = extract_skills("\n".join(required_text))
    pref_skills = extract_skills("\n".join(preferred_text))

    # Ensure no duplicates: skills in req shouldn't be in pref
    pref_skills = [s for s in pref_skills if s not in req_skills]

    # If all skills ended up in one bucket, balance reasonably
    all_skills = extract_skills(text)
    if not req_skills and all_skills:
        req_skills = all_skills[:int(len(all_skills) * 0.7)] or all_skills
        pref_skills = all_skills[int(len(all_skills) * 0.7):]

    return {
        'required_skills': req_skills,
        'preferred_skills': pref_skills
    }


def generate_jd_summary(title: str, text: str, skills: List[str], exp_level: str) -> str:
    """Generates a concise, high-level summary of the job description."""
    key_skills_str = ", ".join(skills[:6]) if skills else "modern software engineering practices"
    exp_text = f"{exp_level.capitalize()} level role"
    return f"Exciting opportunity for a {title}. Seeking engineers proficient in {key_skills_str} for a {exp_text}."


def analyze_job_description(title: str, description: str) -> Dict[str, Any]:
    """
    Main JD analysis pipeline.
    """
    skill_partition = partition_skills_required_vs_preferred(description)
    exp_info = extract_experience_requirements(description)
    edu_info = extract_education_requirements(description)
    all_skills = list(dict.fromkeys(skill_partition['required_skills'] + skill_partition['preferred_skills']))
    categorized = extract_categorized_skills(description)
    summary = generate_jd_summary(title, description, all_skills, exp_info['level'])

    return {
        'title': title,
        'required_skills': skill_partition['required_skills'],
        'preferred_skills': skill_partition['preferred_skills'],
        'all_skills': all_skills,
        'categorized_skills': categorized,
        'experience_years': exp_info['min_years'],
        'experience_level': exp_info['level'],
        'education_requirements': edu_info,
        'ai_summary': summary
    }

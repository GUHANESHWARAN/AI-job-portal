"""
Skill Gap Analysis and Learning Roadmap Engine:
Compares a student's existing skill repertoire against target job requirements or
industry benchmark roles, identifying deficits and generating structured learning paths.
"""

from typing import Any, Dict, List, Optional
from .skill_extractor import SKILL_TO_CATEGORY, calculate_skill_similarity

# Standard benchmark roles and typical requirements
BENCHMARK_ROLES: Dict[str, Dict[str, Any]] = {
    'Full-Stack Python Developer': {
        'core_skills': ['Python', 'Django', 'REST API', 'JavaScript', 'HTML5', 'CSS3', 'MySQL', 'Git'],
        'recommended_skills': ['Docker', 'PostgreSQL', 'Redis', 'React', 'Linux', 'Celery', 'CI/CD'],
        'description': 'Develops robust backend web architectures, relational database schemas, and responsive client interfaces.'
    },
    'Data Scientist & Machine Learning Engineer': {
        'core_skills': ['Python', 'Machine Learning', 'Scikit-Learn', 'Pandas', 'NumPy', 'SQL', 'Git'],
        'recommended_skills': ['Deep Learning', 'PyTorch', 'TensorFlow', 'NLP', 'Computer Vision', 'Docker', 'Power BI'],
        'description': 'Constructs predictive statistical models, machine learning pipelines, and extracts insights from complex datasets.'
    },
    'Frontend Engineer': {
        'core_skills': ['JavaScript', 'TypeScript', 'React', 'HTML5', 'CSS3', 'Tailwind CSS', 'Git'],
        'recommended_skills': ['Next.js', 'Redux', 'Vue.js', 'REST API', 'GraphQL', 'Webpack', 'Figma'],
        'description': 'Specializes in creating accessible, lightning-fast, and responsive user interfaces.'
    },
    'Cloud & DevOps Engineer': {
        'core_skills': ['Linux', 'Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Git', 'Bash'],
        'recommended_skills': ['Terraform', 'Ansible', 'Jenkins', 'Prometheus', 'Grafana', 'Python', 'Nginx'],
        'description': 'Automates deployment pipelines, ensures cloud scalability, infrastructure as code, and system reliability.'
    },
    'Backend Java Engineer': {
        'core_skills': ['Java', 'Spring Boot', 'REST API', 'MySQL', 'SQL', 'Git', 'Microservices'],
        'recommended_skills': ['Docker', 'Kafka', 'Redis', 'Hibernate', 'Kubernetes', 'JUnit', 'AWS'],
        'description': 'Builds enterprise-grade, high-throughput backend services and distributed microservices.'
    }
}

RECOMMENDED_PROJECT_IDEAS = {
    'Django': 'Build a multi-tenant SaaS application or E-Commerce platform with role-based permissions and Stripe integration.',
    'Docker': 'Containerize a multi-service web app (frontend, backend, Redis, MySQL) using Docker Compose with environment variables.',
    'Machine Learning': 'Train and deploy an end-to-end customer churn or recommendation system API using Scikit-Learn and FastAPI.',
    'React': 'Create a dynamic dashboard with dark mode, interactive charts, and real-time WebSocket notifications.',
    'Kubernetes': 'Deploy a microservices architecture on a local Minikube cluster with horizontal pod autoscaling and ingress routing.',
    'Redis': 'Implement caching and rate limiting middleware to decrease database response times under heavy load.'
}


def analyze_skill_gap(
    candidate_skills: List[str],
    target_skills: List[str],
    target_title: str = "Target Position"
) -> Dict[str, Any]:
    """
    Analyzes gaps between candidate skills and target skills, providing a roadmap.
    """
    score, matched, missing = calculate_skill_similarity(candidate_skills, target_skills)

    # Classify missing skills by priority
    high_priority = []
    medium_priority = []

    for s in missing:
        cat = SKILL_TO_CATEGORY.get(s.lower(), '')
        if cat in ('Programming Languages', 'Web & Frameworks', 'AI / ML & Data Science'):
            high_priority.append(s)
        else:
            medium_priority.append(s)

    # Readiness Assessment
    if score >= 80:
        readiness = "Job Ready"
        readiness_badge = "success"
        readiness_message = "You have the primary skills required for this role. Focus on practicing interview questions and system design."
        estimated_weeks = 2
    elif score >= 50:
        readiness = "Needs Targeted Upskilling"
        readiness_badge = "warning"
        readiness_message = f"You possess solid foundational skills. Bridging gaps in {', '.join(missing[:3])} will make you a prime candidate."
        estimated_weeks = 4
    else:
        readiness = "Foundational Stage"
        readiness_badge = "danger"
        readiness_message = "Substantial skill acquisition recommended. Follow the milestone roadmap below to build practical expertise."
        estimated_weeks = 8

    # Generate Learning Milestones Roadmap
    roadmap = []
    step = 1

    if high_priority:
        roadmap.append({
            'step': step,
            'title': 'Core Technical Foundations',
            'timeframe': f'Weeks 1-{max(2, estimated_weeks // 3)}',
            'focus_skills': high_priority[:4],
            'action': f"Master the core syntax, standard libraries, and fundamental patterns of {', '.join(high_priority[:3])}.",
            'resources': [f"Official documentation and interactive tutorials for {s}" for s in high_priority[:3]]
        })
        step += 1

    if medium_priority:
        roadmap.append({
            'step': step,
            'title': 'Tools, Databases & Infrastructure',
            'timeframe': f'Weeks {max(2, estimated_weeks // 3) + 1}-{max(4, 2 * estimated_weeks // 3)}',
            'focus_skills': medium_priority[:4],
            'action': f"Integrate production tooling: {', '.join(medium_priority[:3])} into your workflow.",
            'resources': [f"Hands-on labs and practical configuration guides for {s}" for s in medium_priority[:3]]
        })
        step += 1

    # Project Milestone
    suggested_projects = []
    for s in missing:
        if s in RECOMMENDED_PROJECT_IDEAS:
            suggested_projects.append({'skill': s, 'idea': RECOMMENDED_PROJECT_IDEAS[s]})
    if not suggested_projects:
        suggested_projects.append({
            'skill': target_title,
            'idea': f"Develop an end-to-end production-ready capstone project demonstrating integration of {', '.join((matched + missing)[:4])}."
        })

    roadmap.append({
        'step': step,
        'title': 'Portfolio Project & Practical Demonstration',
        'timeframe': f'Weeks {max(3, 2 * estimated_weeks // 3) + 1}-{estimated_weeks}',
        'focus_skills': (missing[:3] or matched[:3]),
        'action': 'Implement a comprehensive portfolio project showcasing clean code, unit tests, and CI/CD deployment.',
        'suggested_projects': suggested_projects[:2]
    })

    return {
        'target_title': target_title,
        'readiness_score': score,
        'readiness_level': readiness,
        'readiness_badge': readiness_badge,
        'readiness_message': readiness_message,
        'estimated_weeks': estimated_weeks,
        'matched_skills': matched,
        'missing_skills': missing,
        'high_priority_missing': high_priority,
        'medium_priority_missing': medium_priority,
        'roadmap': roadmap
    }


def get_available_benchmark_roles() -> Dict[str, Dict[str, Any]]:
    """Returns the catalog of preset industry benchmark roles."""
    return BENCHMARK_ROLES

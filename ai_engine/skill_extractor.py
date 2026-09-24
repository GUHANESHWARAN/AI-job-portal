"""
Skill Extraction Engine with comprehensive taxonomy and boundary-safe matching.
Extracts technical skills, frameworks, tools, and soft skills with categorization.
"""

import re
from typing import Dict, List, Set, Tuple

# Comprehensive taxonomy categorized by domain
SKILL_TAXONOMY = {
    'Programming Languages': [
        'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'C', 'Go', 'Golang',
        'Rust', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'R', 'Scala', 'Dart', 'SQL',
        'HTML', 'HTML5', 'CSS', 'CSS3', 'Bash', 'Shell', 'PowerShell', 'Perl', 'MATLAB'
    ],
    'Web & Frameworks': [
        'Django', 'Flask', 'FastAPI', 'React', 'React.js', 'Angular', 'Vue', 'Vue.js',
        'Next.js', 'Node.js', 'Express.js', 'Spring Boot', 'ASP.NET', 'Laravel',
        'Ruby on Rails', 'Svelte', 'Tailwind CSS', 'Bootstrap', 'jQuery', 'Redux',
        'GraphQL', 'REST API', 'RESTful APIs', 'WebSockets', 'Celery', 'Gunicorn', 'Jinja2'
    ],
    'Databases & Storage': [
        'MySQL', 'PostgreSQL', 'SQLite', 'MongoDB', 'Redis', 'Cassandra', 'Oracle',
        'Microsoft SQL Server', 'DynamoDB', 'Elasticsearch', 'Firebase', 'MariaDB',
        'Neo4j', 'Snowflake', 'Supabase'
    ],
    'Cloud & DevOps': [
        'AWS', 'Amazon Web Services', 'Azure', 'Microsoft Azure', 'Google Cloud', 'GCP',
        'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'Jenkins', 'GitHub Actions',
        'GitLab CI', 'Linux', 'Ubuntu', 'Nginx', 'Apache', 'CI/CD', 'Microservices',
        'Prometheus', 'Grafana', 'Serverless', 'Helm', 'Vagrant'
    ],
    'AI / ML & Data Science': [
        'Machine Learning', 'Deep Learning', 'Artificial Intelligence', 'Data Science',
        'Natural Language Processing', 'NLP', 'Computer Vision', 'PyTorch', 'TensorFlow',
        'Keras', 'Scikit-Learn', 'Pandas', 'NumPy', 'SciPy', 'Matplotlib', 'Seaborn',
        'OpenCV', 'Hugging Face', 'Transformers', 'Sentence Transformers', 'spaCy', 'NLTK',
        'LLM', 'LangChain', 'RAG', 'Vector Database', 'Data Analysis', 'Data Engineering',
        'Apache Spark', 'Hadoop', 'Power BI', 'Tableau', 'BigQuery', 'Feature Engineering',
        'XGBoost', 'LightGBM', 'Reinforcement Learning', 'BERT', 'Generative AI'
    ],
    'Developer Tools & Practices': [
        'Git', 'GitHub', 'GitLab', 'Bitbucket', 'Jira', 'Agile', 'Scrum', 'Kanban',
        'VS Code', 'Postman', 'PyTest', 'UnitTest', 'JUnit', 'Selenium', 'Docker Compose',
        'Figma', 'Swagger', 'OpenAPI', 'Maven', 'Gradle', 'Webpack', 'Vite', 'Kafka',
        'RabbitMQ', 'Object-Oriented Programming', 'OOP', 'Data Structures', 'Algorithms',
        'System Design', 'Design Patterns'
    ],
    'Cybersecurity & Networks': [
        'Cybersecurity', 'Network Security', 'Cryptography', 'Penetration Testing',
        'Ethical Hacking', 'OWASP', 'SSL/TLS', 'OAuth', 'JWT', 'Firewalls', 'Wireshark'
    ],
    'Soft Skills': [
        'Communication', 'Leadership', 'Problem Solving', 'Critical Thinking', 'Teamwork',
        'Time Management', 'Adaptability', 'Collaboration', 'Public Speaking', 'Mentoring',
        'Negotiation', 'Conflict Resolution', 'Project Management'
    ]
}

# Inverted mapping for quick category lookup
SKILL_TO_CATEGORY: Dict[str, str] = {}
ALL_SKILLS: Set[str] = set()

for category, skill_list in SKILL_TAXONOMY.items():
    for skill in skill_list:
        ALL_SKILLS.add(skill)
        SKILL_TO_CATEGORY[skill.lower()] = category

# Pre-compile regex patterns for boundary matching
# Handlers for tricky short words or special characters like C, C++, C#, .NET
SPECIAL_PATTERNS = {
    'c++': re.compile(r'(?i)(?<![a-z0-9])c\+\+(?![a-z0-9])'),
    'c#': re.compile(r'(?i)(?<![a-z0-9])c#(?![a-z0-9])'),
    'c': re.compile(r'\b[C]\b'),  # Uppercase standalone C
    'r': re.compile(r'\b[R]\b'),  # Uppercase standalone R
    'go': re.compile(r'\b(Go|Golang)\b', re.IGNORECASE),
    '.net': re.compile(r'(?i)(?<![a-z0-9])\.net(?![a-z0-9])'),
    'asp.net': re.compile(r'(?i)(?<![a-z0-9])asp\.net(?![a-z0-9])'),
    'node.js': re.compile(r'(?i)\bnode(\.js)?\b'),
    'vue.js': re.compile(r'(?i)\bvue(\.js)?\b'),
    'react.js': re.compile(r'(?i)\breact(\.js)?\b'),
    'ci/cd': re.compile(r'(?i)\bci/cd\b'),
    'rest api': re.compile(r'(?i)\brest(ful)?\s*apis?\b'),
}

GENERAL_PATTERNS: List[Tuple[str, re.Pattern]] = []
for skill in sorted(ALL_SKILLS, key=lambda s: len(s), reverse=True):
    key = skill.lower()
    if key in SPECIAL_PATTERNS:
        continue
    # Safe boundary: not preceded or followed by alphanumeric or underscore
    escaped = re.escape(skill)
    pat = re.compile(rf'(?i)(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])')
    GENERAL_PATTERNS.append((skill, pat))


def extract_skills(text: str) -> List[str]:
    """
    Extracts all recognized skills from raw text preserving proper capitalization.
    Deduplicates results.
    """
    if not text:
        return []

    found_skills: Set[str] = set()

    # Check special patterns first
    for skill_key, pattern in SPECIAL_PATTERNS.items():
        if pattern.search(text):
            # Match back to official casing
            canonical = next((s for s in ALL_SKILLS if s.lower() == skill_key), skill_key.title())
            found_skills.add(canonical)

    # Check general patterns
    for canonical_name, pattern in GENERAL_PATTERNS:
        if pattern.search(text):
            found_skills.add(canonical_name)

    return sorted(list(found_skills))


def extract_categorized_skills(text: str) -> Dict[str, List[str]]:
    """
    Extracts skills and organizes them by domain category.
    """
    skills = extract_skills(text)
    categorized: Dict[str, List[str]] = {cat: [] for cat in SKILL_TAXONOMY.keys()}

    for skill in skills:
        cat = SKILL_TO_CATEGORY.get(skill.lower(), 'Developer Tools & Practices')
        if cat in categorized:
            categorized[cat].append(skill)
        else:
            categorized.setdefault('Other Technical', []).append(skill)

    # Filter out empty categories
    return {k: v for k, v in categorized.items() if v}


def calculate_skill_similarity(candidate_skills: List[str], required_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    """
    Calculates Jaccard-based match percentage between candidate skills and required skills.
    Returns (score_percentage, matched_skills, missing_skills).
    """
    if not required_skills:
        return 100.0, candidate_skills, []

    cand_set = {s.strip().lower() for s in candidate_skills if s.strip()}
    req_map = {s.strip().lower(): s.strip() for s in required_skills if s.strip()}

    matched = []
    missing = []

    for req_lower, req_orig in req_map.items():
        if req_lower in cand_set:
            matched.append(req_orig)
        else:
            missing.append(req_orig)

    score = (len(matched) / len(req_map)) * 100.0 if req_map else 100.0
    return round(score, 1), matched, missing


from django.test import TestCase
from ai_engine.skill_extractor import (
    extract_skills, extract_categorized_skills, calculate_skill_similarity
)
from ai_engine.resume_analyzer import (
    extract_contact_info, segment_resume_sections, calculate_ats_score
)
from ai_engine.jd_analyzer import (
    analyze_job_description, extract_experience_requirements
)
from ai_engine.matcher import (
    compute_job_match, calculate_semantic_similarity
)
from ai_engine.skill_gap import (
    analyze_skill_gap, get_available_benchmark_roles
)


class AiEngineTestCase(TestCase):
    def test_skill_extraction(self):
        sample_text = (
            "Senior Software Engineer with 5+ years of experience in Python, Django, and MySQL. "
            "Proficient in Docker containerization, REST API design, and Git version control. "
            "Familiar with Machine Learning baselines in Scikit-Learn and Pandas."
        )
        skills = extract_skills(sample_text)
        self.assertIn('Python', skills)
        self.assertIn('Django', skills)
        self.assertIn('MySQL', skills)
        self.assertIn('Docker', skills)
        self.assertIn('REST API', skills)
        self.assertIn('Machine Learning', skills)
        self.assertIn('Scikit-Learn', skills)

    def test_skill_boundary_safety(self):
        # "React" shouldn't trigger standalone "C" or "R" falsely
        sample_text = "I love React and creating modern frontends."
        skills = extract_skills(sample_text)
        self.assertIn('React', skills)
        self.assertNotIn('C', skills)

    def test_categorized_skills(self):
        sample_text = "Experienced in Python, Django, MySQL, AWS, and Git."
        cats = extract_categorized_skills(sample_text)
        self.assertIn('Programming Languages', cats)
        self.assertIn('Python', cats['Programming Languages'])
        self.assertIn('Web & Frameworks', cats)
        self.assertIn('Django', cats['Web & Frameworks'])

    def test_contact_info_extraction(self):
        text = """
        John Doe
        Email: john.doe@university.edu
        Phone: +91 98765 43210
        LinkedIn: https://linkedin.com/in/johndoe
        GitHub: https://github.com/johndoe
        """
        contact = extract_contact_info(text)
        self.assertEqual(contact['email'], 'john.doe@university.edu')
        self.assertIn('98765', contact['phone'])
        self.assertIn('johndoe', contact['linkedin'])
        self.assertIn('johndoe', contact['github'])

    def test_ats_score_calculation(self):
        text = """
        Arjun Patel
        Email: arjun@test.com | Phone: 9876543210 | LinkedIn: linkedin.com/in/arjun
        
        Summary
        Experienced software engineer with expertise in building scalable applications.
        
        Education
        B.Tech Computer Science, National Institute of Technology, 2026.
        
        Experience
        Developed full-stack web application using Django and MySQL. Improved query performance by 40%.
        Architected RESTful APIs serving 10,000+ requests daily.
        
        Technical Skills
        Python, Django, MySQL, PostgreSQL, Docker, Git, Redis, Linux, REST API, Machine Learning.
        
        Projects
        Built an e-commerce platform with automated payment webhooks.
        """
        contact = extract_contact_info(text)
        sections = segment_resume_sections(text)
        skills = extract_skills(text)
        ats_result = calculate_ats_score(text, contact, sections, skills)

        self.assertGreaterEqual(ats_result['score'], 75)
        self.assertGreaterEqual(ats_result['metrics_count'], 1)
        self.assertGreaterEqual(ats_result['action_verbs_count'], 2)

    def test_jd_analyzer(self):
        jd_text = """
        We are seeking a Python Backend Developer with 3+ years experience.
        Requirements:
        Must have proficiency in Python, Django, and MySQL.
        Strong understanding of REST API and Docker.
        
        Nice to have:
        Familiarity with AWS, Redis, and Celery is a plus.
        """
        analysis = analyze_job_description("Python Backend Developer", jd_text)
        self.assertEqual(analysis['experience_years'], 3)
        self.assertEqual(analysis['experience_level'], 'mid')
        self.assertIn('Python', analysis['required_skills'])
        self.assertIn('Django', analysis['required_skills'])

    def test_matcher_multi_factor(self):
        cand_skills = ['Python', 'Django', 'MySQL', 'Docker', 'Git']
        resume_text = "Backend developer specializing in Python and Django APIs with MySQL databases."
        req_skills = ['Python', 'Django', 'MySQL', 'Docker']
        pref_skills = ['AWS', 'Kubernetes']
        job_desc = "Looking for a backend Python engineer with Django and MySQL skills."

        match = compute_job_match(
            candidate_skills=cand_skills,
            resume_text=resume_text,
            job_required_skills=req_skills,
            job_preferred_skills=pref_skills,
            job_description=job_desc,
            job_exp_level='entry',
            job_min_years=0
        )

        self.assertGreaterEqual(match['overall_score'], 70.0)
        self.assertIn('Python', match['matched_required'])
        self.assertIn(match['verdict_badge'], ['primary', 'success'])
        self.assertTrue(len(match['summary_explanation']) > 10)

    def test_skill_gap_and_roadmap(self):
        cand_skills = ['Python', 'MySQL']
        target_skills = ['Python', 'Django', 'REST API', 'Docker', 'MySQL']

        gap = analyze_skill_gap(cand_skills, target_skills, "Full Stack Developer")
        self.assertIn('Django', gap['missing_skills'])
        self.assertIn('REST API', gap['missing_skills'])
        self.assertIn('Docker', gap['missing_skills'])
        self.assertTrue(len(gap['roadmap']) >= 2)
        self.assertIn('roadmap', gap)

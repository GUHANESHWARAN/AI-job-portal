"""
Database Seeder Command for CareerAI:
Populates realistic companies, recruiters, students, job postings, internships, and applications.
"""

from django.core.management.base import BaseCommand
from accounts.models import User
from companies.models import Company
from recruiters.models import RecruiterProfile
from students.models import StudentProfile
from jobs.models import Job
from applications.models import Application
from ai_engine.matcher import compute_job_match


class Command(BaseCommand):
    help = "Seeds database with realistic demo data for testing and demonstrations."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Starting database seeding..."))

        # 1. Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@careerai.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('adminpassword123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user (admin / adminpassword123)"))

        # 2. Companies
        google, _ = Company.objects.get_or_create(
            name="Google",
            defaults={
                'industry': 'Artificial Intelligence & Cloud Computing',
                'company_size': '1000+',
                'location': 'Bengaluru, India / Mountain View, CA',
                'website': 'https://careers.google.com',
                'description': 'Google is a global technology leader focused on improving the ways people connect with information. Engineering teams develop next-generation search, AI, cloud, and mobile ecosystems.'
            }
        )

        stripe, _ = Company.objects.get_or_create(
            name="Stripe",
            defaults={
                'industry': 'Financial Technology & Payments Infrastructure',
                'company_size': '1000+',
                'location': 'Bengaluru, India / Remote',
                'website': 'https://stripe.com/jobs',
                'description': 'Stripe is a financial infrastructure platform for businesses. Millions of companies use Stripe to accept payments, grow their revenue, and accelerate new business opportunities.'
            }
        )

        microsoft, _ = Company.objects.get_or_create(
            name="Microsoft",
            defaults={
                'industry': 'Enterprise Cloud & Operating Systems',
                'company_size': '1000+',
                'location': 'Hyderabad, India / Redmond, WA',
                'website': 'https://careers.microsoft.com',
                'description': 'Microsoft enables digital transformation for the era of an intelligent cloud and an intelligent edge. Its mission is to empower every person and organization on the planet to achieve more.'
            }
        )

        zomato, _ = Company.objects.get_or_create(
            name="Zomato",
            defaults={
                'industry': 'Consumer Technology & Logistics',
                'company_size': '1000+',
                'location': 'Gurugram, India',
                'website': 'https://zomato.com/careers',
                'description': 'Zomato is a leading technology platform connecting customers, restaurant partners, and delivery partners.'
            }
        )

        # 3. Recruiters
        rec_google_user, created = User.objects.get_or_create(
            username='recruiter_google',
            defaults={
                'email': 'priya.sharma@google.com',
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'role': User.ROLE_RECRUITER,
            }
        )
        if created:
            rec_google_user.set_password('recruiter123')
            rec_google_user.save()

        rec_google_prof, _ = RecruiterProfile.objects.get_or_create(user=rec_google_user)
        rec_google_prof.company = google
        rec_google_prof.designation = "Lead Technical Recruiter"
        rec_google_prof.department = "Google Cloud & AI Engineering"
        rec_google_prof.linkedin_url = "https://linkedin.com/in/priyasharma-recruiter"
        rec_google_prof.save()

        rec_stripe_user, created = User.objects.get_or_create(
            username='recruiter_stripe',
            defaults={
                'email': 'alex.vance@stripe.com',
                'first_name': 'Alex',
                'last_name': 'Vance',
                'role': User.ROLE_RECRUITER,
            }
        )
        if created:
            rec_stripe_user.set_password('recruiter123')
            rec_stripe_user.save()

        rec_stripe_prof, _ = RecruiterProfile.objects.get_or_create(user=rec_stripe_user)
        rec_stripe_prof.company = stripe
        rec_stripe_prof.designation = "Senior Talent Acquisition Partner"
        rec_stripe_prof.department = "Global Payments Infrastructure"
        rec_stripe_prof.linkedin_url = "https://linkedin.com/in/alexvance-talent"
        rec_stripe_prof.save()

        # 4. Students
        students_data = [
            {
                'username': 'student_arjun',
                'email': 'arjun.patel@gmail.com',
                'first_name': 'Arjun',
                'last_name': 'Patel',
                'headline': 'Full-Stack Python Engineer | Backend Architecture Specialist',
                'degree': 'B.Tech in Computer Science and Engineering',
                'institution': 'Indian Institute of Technology (IIT) Madras',
                'graduation_year': 2026,
                'cgpa': 8.95,
                'skills': 'Python, Django, REST API, MySQL, PostgreSQL, Docker, Git, Redis, Linux, Celery',
                'bio': 'Passionate software engineering undergraduate specializing in high-throughput backend services, relational database optimization, and cloud containerization with Docker.',
                'ats_score': 88,
            },
            {
                'username': 'student_ananya',
                'email': 'ananya.iyer@gmail.com',
                'first_name': 'Ananya',
                'last_name': 'Iyer',
                'headline': 'Data Scientist & Machine Learning Engineer | Deep Learning Enthusiast',
                'degree': 'B.Tech in Artificial Intelligence & Data Science',
                'institution': 'National Institute of Technology (NIT) Trichy',
                'graduation_year': 2026,
                'cgpa': 9.20,
                'skills': 'Python, Machine Learning, Deep Learning, PyTorch, Scikit-Learn, Pandas, NumPy, SQL, NLP, Computer Vision',
                'bio': 'Aspiring AI Researcher with experience in natural language processing transformers, statistical feature engineering, and predictive regression models.',
                'ats_score': 92,
            },
            {
                'username': 'student_rohit',
                'email': 'rohit.sharma@gmail.com',
                'first_name': 'Rohit',
                'last_name': 'Sharma',
                'headline': 'Frontend Engineer | Modern React & UI/UX Craftsman',
                'degree': 'B.E. in Information Technology',
                'institution': 'Delhi Technological University (DTU)',
                'graduation_year': 2026,
                'cgpa': 8.40,
                'skills': 'JavaScript, TypeScript, React, HTML5, CSS3, Tailwind CSS, Next.js, Redux, Git, Figma',
                'bio': 'Frontend engineer obsessed with sub-second page loads, accessibility standards, responsive design systems, and state management.',
                'ats_score': 82,
            },
            {
                'username': 'student_sneha',
                'email': 'sneha.nair@gmail.com',
                'first_name': 'Sneha',
                'last_name': 'Nair',
                'headline': 'Cloud & DevOps Practitioner | Kubernetes & CI/CD Builder',
                'degree': 'B.Tech in Computer Science',
                'institution': 'Vellore Institute of Technology (VIT)',
                'graduation_year': 2025,
                'cgpa': 8.70,
                'skills': 'Linux, Docker, Kubernetes, AWS, CI/CD, Git, Bash, Terraform, Python, Prometheus',
                'bio': 'DevOps enthusiast skilled in infrastructure automation, cloud deployment pipelines, container orchestration, and telemetry monitoring.',
                'ats_score': 85,
            }
        ]

        created_students = {}
        for sdata in students_data:
            suser, created = User.objects.get_or_create(
                username=sdata['username'],
                defaults={
                    'email': sdata['email'],
                    'first_name': sdata['first_name'],
                    'last_name': sdata['last_name'],
                    'role': User.ROLE_STUDENT
                }
            )
            if created:
                suser.set_password('student123')
                suser.save()

            sprof, _ = StudentProfile.objects.get_or_create(user=suser)
            sprof.headline = sdata['headline']
            sprof.degree = sdata['degree']
            sprof.institution = sdata['institution']
            sprof.graduation_year = sdata['graduation_year']
            sprof.cgpa = sdata['cgpa']
            sprof.skills = sdata['skills']
            sprof.bio = sdata['bio']
            sprof.ats_score = sdata['ats_score']
            sprof.extracted_skills = [s.strip() for s in sdata['skills'].split(',') if s.strip()]
            sprof.parsed_resume_text = f"{sdata['first_name']} {sdata['last_name']}\n{sdata['degree']} - {sdata['institution']}\nSkills: {sdata['skills']}\nSummary: {sdata['bio']}"
            sprof.save()
            created_students[sdata['username']] = sprof

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(created_students)} student profiles."))

        # 5. Jobs & Internships
        jobs_data = [
            {
                'title': 'Senior Backend Engineer (Python / Django)',
                'recruiter': rec_stripe_user,
                'company': stripe,
                'job_type': Job.JOB_TYPE_FULL_TIME,
                'work_mode': Job.WORK_MODE_REMOTE,
                'location': 'Bengaluru, India / Remote',
                'experience_level': Job.EXP_MID,
                'min_experience_years': 2,
                'salary_min': 1800000,
                'salary_max': 2600000,
                'required_skills': ['Python', 'Django', 'REST API', 'MySQL', 'Docker', 'Git'],
                'preferred_skills': ['PostgreSQL', 'Redis', 'Celery', 'AWS'],
                'description': 'Stripe is looking for a Backend Engineer to build resilient payment processing APIs. You will design data models, implement idempotent webhooks, and optimize MySQL query performance.',
                'responsibilities': 'Architect clean RESTful services; maintain high availability systems; write automated unit and integration tests; collaborate with frontend engineers.',
                'requirements': 'Strong proficiency in Python and Django; hands-on relational database experience (MySQL/PostgreSQL); experience with containerized microservices (Docker).'
            },
            {
                'title': 'Machine Learning Engineer (NLP & Recommendations)',
                'recruiter': rec_google_user,
                'company': google,
                'job_type': Job.JOB_TYPE_FULL_TIME,
                'work_mode': Job.WORK_MODE_HYBRID,
                'location': 'Bengaluru, India',
                'experience_level': Job.EXP_ENTRY,
                'min_experience_years': 1,
                'salary_min': 2200000,
                'salary_max': 3200000,
                'required_skills': ['Python', 'Machine Learning', 'PyTorch', 'Scikit-Learn', 'Pandas', 'SQL'],
                'preferred_skills': ['Deep Learning', 'NLP', 'Transformers', 'Docker', 'Google Cloud'],
                'description': 'Join Google AI Engineering to develop cutting-edge recommendation models and neural text pipelines processing millions of queries every minute.',
                'responsibilities': 'Design feature pipelines; train deep learning architectures; benchmark model accuracy and inference latency; deploy models to production endpoints.',
                'requirements': 'BS/MS in Computer Science or quantitative field; proficient in PyTorch, Scikit-Learn, and Python; understanding of embeddings and semantic search.'
            },
            {
                'title': 'Frontend Engineer (React & TypeScript)',
                'recruiter': rec_stripe_user,
                'company': zomato,
                'job_type': Job.JOB_TYPE_FULL_TIME,
                'work_mode': Job.WORK_MODE_ONSITE,
                'location': 'Gurugram, India',
                'experience_level': Job.EXP_ENTRY,
                'min_experience_years': 0,
                'salary_min': 1200000,
                'salary_max': 1800000,
                'required_skills': ['JavaScript', 'TypeScript', 'React', 'HTML5', 'CSS3', 'Git'],
                'preferred_skills': ['Next.js', 'Tailwind CSS', 'Redux', 'Figma'],
                'description': 'Create intuitive, blazing-fast web customer interfaces that millions of diners use daily to discover food and track deliveries in real time.',
                'responsibilities': 'Develop reusable React component libraries; optimize browser rendering performance; collaborate closely with product designers.',
                'requirements': 'Demonstrated experience building responsive web interfaces in React and TypeScript; solid understanding of CSS layouts and modern browser DOM.'
            },
            {
                'title': 'Cloud & DevOps Automation Specialist',
                'recruiter': rec_google_user,
                'company': microsoft,
                'job_type': Job.JOB_TYPE_FULL_TIME,
                'work_mode': Job.WORK_MODE_HYBRID,
                'location': 'Hyderabad, India',
                'experience_level': Job.EXP_MID,
                'min_experience_years': 2,
                'salary_min': 1600000,
                'salary_max': 2400000,
                'required_skills': ['Linux', 'Docker', 'Kubernetes', 'CI/CD', 'Git', 'Bash'],
                'preferred_skills': ['AWS', 'Azure', 'Terraform', 'Prometheus', 'Python'],
                'description': 'Scale Azure enterprise platform clusters. Drive infrastructure-as-code initiatives, streamline continuous integration, and monitor telemetry across hundreds of nodes.',
                'responsibilities': 'Automate Kubernetes deployments; build robust CI/CD pipelines; configure alerts and Prometheus metric scrapers.',
                'requirements': 'Experience managing production Linux environments, container orchestration with Kubernetes, and scripting in Bash or Python.'
            },
            {
                'title': 'AI & Machine Learning Summer Intern 2026',
                'recruiter': rec_google_user,
                'company': google,
                'job_type': Job.JOB_TYPE_INTERNSHIP,
                'work_mode': Job.WORK_MODE_HYBRID,
                'location': 'Bengaluru, India',
                'experience_level': Job.EXP_INTERN,
                'min_experience_years': 0,
                'salary_min': 75000,
                'salary_max': 100000,
                'required_skills': ['Python', 'Machine Learning', 'NumPy', 'Pandas', 'Git'],
                'preferred_skills': ['Scikit-Learn', 'PyTorch', 'SQL'],
                'description': 'Spend 10 weeks working alongside Google Research scientists on novel exploratory machine learning architectures. Mentorship provided by senior staff researchers.',
                'responsibilities': 'Conduct literature reviews; implement benchmark ML baselines; analyze experimental data using Pandas and Matplotlib.',
                'requirements': 'Currently enrolled in an undergraduate or graduate degree in Computer Science, Data Science, or related field with graduation in 2026.'
            },
            {
                'title': 'Software Engineering Intern (Backend & APIs)',
                'recruiter': rec_stripe_user,
                'company': stripe,
                'job_type': Job.JOB_TYPE_INTERNSHIP,
                'work_mode': Job.WORK_MODE_REMOTE,
                'location': 'Bengaluru, India / Remote',
                'experience_level': Job.EXP_INTERN,
                'min_experience_years': 0,
                'salary_min': 60000,
                'salary_max': 85000,
                'required_skills': ['Python', 'Django', 'MySQL', 'Git', 'REST API'],
                'preferred_skills': ['Docker', 'Linux'],
                'description': 'Stripe summer engineering internship. Ship real code to production that touches global payment processing within your first three weeks.',
                'responsibilities': 'Build RESTful API endpoints; write comprehensive unit tests; participate in engineering sprint planning and code reviews.',
                'requirements': 'Fundamental coursework in Object-Oriented Programming, Data Structures & Algorithms, and relational database concepts.'
            }
        ]

        created_jobs = []
        for jdata in jobs_data:
            job, _ = Job.objects.get_or_create(
                title=jdata['title'],
                company=jdata['company'],
                defaults={
                    'recruiter': jdata['recruiter'],
                    'job_type': jdata['job_type'],
                    'work_mode': jdata['work_mode'],
                    'location': jdata['location'],
                    'experience_level': jdata['experience_level'],
                    'min_experience_years': jdata['min_experience_years'],
                    'salary_min': jdata['salary_min'],
                    'salary_max': jdata['salary_max'],
                    'required_skills': jdata['required_skills'],
                    'preferred_skills': jdata['preferred_skills'],
                    'description': jdata['description'],
                    'responsibilities': jdata['responsibilities'],
                    'requirements': jdata['requirements'],
                    'status': Job.STATUS_ACTIVE
                }
            )
            created_jobs.append(job)

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(created_jobs)} jobs and internships."))

        # 6. Sample Applications with computed AI Match Scores
        # Arjun -> Stripe Backend Job & Stripe Intern
        stripe_backend_job = next((j for j in created_jobs if 'Stripe' in j.company.name and 'Backend' in j.title), None)
        google_ml_job = next((j for j in created_jobs if 'Google' in j.company.name and 'Machine Learning' in j.title), None)
        google_ai_intern = next((j for j in created_jobs if 'Summer Intern' in j.title), None)

        application_pairs = [
            (created_students['student_arjun'], stripe_backend_job, Application.STATUS_SHORTLISTED, "Candidate has strong hands-on Django and MySQL experience."),
            (created_students['student_ananya'], google_ml_job, Application.STATUS_INTERVIEW, "Outstanding PyTorch project background. Scheduled for technical interview."),
            (created_students['student_ananya'], google_ai_intern, Application.STATUS_SHORTLISTED, "Top candidate for summer internship cohort."),
            (created_students['student_sneha'], next((j for j in created_jobs if 'DevOps' in j.title), None), Application.STATUS_REVIEWING, "Good Kubernetes background; evaluating system design."),
            (created_students['student_rohit'], next((j for j in created_jobs if 'Frontend' in j.title), None), Application.STATUS_APPLIED, ""),
        ]

        app_count = 0
        for student_prof, job_obj, status, notes in application_pairs:
            if not job_obj or not student_prof:
                continue

            cand_skills = student_prof.get_skills_list()
            resume_text = student_prof.parsed_resume_text
            match_info = compute_job_match(
                candidate_skills=cand_skills,
                resume_text=resume_text,
                job_required_skills=job_obj.required_skills,
                job_preferred_skills=job_obj.preferred_skills,
                job_description=f"{job_obj.title} {job_obj.description} {job_obj.requirements}",
                job_exp_level=job_obj.experience_level,
                job_min_years=job_obj.min_experience_years
            )

            app, created = Application.objects.get_or_create(
                student=student_prof.user,
                job=job_obj,
                defaults={
                    'overall_match_score': match_info['overall_score'],
                    'skill_match_score': match_info['skill_score'],
                    'semantic_match_score': match_info['semantic_score'],
                    'experience_match_score': match_info['experience_score'],
                    'match_explanation': match_info,
                    'status': status,
                    'recruiter_notes': notes,
                    'cover_letter': f"I am excited to apply for {job_obj.title} at {job_obj.company.name}. My academic coursework and projects directly align with your requirements."
                }
            )
            if created:
                app_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {app_count} candidate applications with live AI match scores."))
        self.stdout.write(self.style.SUCCESS("All seed data created successfully!"))

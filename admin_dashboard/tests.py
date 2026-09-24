from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from companies.models import Company
from jobs.models import Job
from applications.models import Application
from students.models import StudentProfile


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin_test@example.com',
            password='Password123!',
            role=User.ROLE_ADMIN,
        )
        self.student_user = User.objects.create_user(
            username='student_test',
            email='student_test@example.com',
            password='Password123!',
            role=User.ROLE_STUDENT,
        )
        # Profile is auto-created by signal on user creation
        self.student_profile = StudentProfile.objects.get(user=self.student_user)
        self.student_profile.skills = 'Python,Django,SQL'
        self.student_profile.save()

        self.recruiter_user = User.objects.create_user(
            username='recruiter_test',
            email='recruiter_test@example.com',
            password='Password123!',
            role=User.ROLE_RECRUITER,
        )
        self.company = Company.objects.create(
            name='Test Corp',
            slug='test-corp',
            website='https://test.corp',
            description='Test company',
        )
        self.job = Job.objects.create(
            title='Software Engineer',
            company=self.company,
            recruiter=self.recruiter_user,
            job_type=Job.JOB_TYPE_FULL_TIME,
            work_mode=Job.WORK_MODE_REMOTE,
            status=Job.STATUS_ACTIVE,
            description='Test job',
            required_skills='Python,Django',
        )
        self.internship = Job.objects.create(
            title='Backend Intern',
            company=self.company,
            recruiter=self.recruiter_user,
            job_type=Job.JOB_TYPE_INTERNSHIP,
            work_mode=Job.WORK_MODE_REMOTE,
            status=Job.STATUS_ACTIVE,
            description='Internship',
            required_skills='Python',
        )
        self.application = Application.objects.create(
            job=self.job,
            student=self.student_user,
            status=Application.STATUS_APPLIED,
            overall_match_score=85,
        )

    def test_anonymous_redirected_from_admin(self):
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp['Location'])

    def test_student_forbidden_from_admin(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/')

    def test_recruiter_forbidden_from_admin(self):
        self.client.force_login(self.recruiter_user)
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/')

    def test_admin_can_access_all_pages(self):
        self.client.force_login(self.admin)
        pages = [
            ('admin_dashboard', []),
            ('admin_students', []),
            ('admin_recruiters', []),
            ('admin_companies', []),
            ('admin_jobs', []),
            ('admin_internships', []),
            ('admin_applications', []),
            ('admin_ai_insights', []),
            ('admin_analytics', []),
            ('admin_reports', []),
            ('admin_activity_logs', []),
            ('admin_settings', []),
            ('admin_student_detail', [self.student_user.id]),
            ('admin_recruiter_detail', [self.recruiter_user.id]),
            ('admin_company_detail', [self.company.id]),
        ]
        for name, args in pages:
            url = reverse(name, args=args)
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, f'Failed on {name} ({url})')


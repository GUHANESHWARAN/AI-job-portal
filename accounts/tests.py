from django.test import TestCase
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from jobs.models import Job
from companies.models import Company

# Create your tests here.

class WebFlowTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(name="Acme Corp", industry="Tech")
        self.recruiter_user = User.objects.create_user(
            username="test_recruiter", password="password123", role=User.ROLE_RECRUITER
        )
        self.student_user = User.objects.create_user(
            username="test_student", password="password123", role=User.ROLE_STUDENT
        )
        self.job = Job.objects.create(
            title="Software Engineer",
            company=self.company,
            recruiter=self.recruiter_user,
            job_type=Job.JOB_TYPE_FULL_TIME,
            description="Sample description for engineering position.",
            required_skills=["Python", "Django"]
        )

    def test_homepage_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CareerAI")

    def test_job_list_loads(self):
        response = self.client.get(reverse('job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")

    def test_job_detail_loads(self):
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")

    def test_student_login_and_dashboard_redirect(self):
        login_success = self.client.login(username="test_student", password="password123")
        self.assertTrue(login_success)
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_recruiter_login_and_dashboard_redirect(self):
        login_success = self.client.login(username="test_recruiter", password="password123")
        self.assertTrue(login_success)
        response = self.client.get(reverse('recruiter_dashboard'))
        self.assertEqual(response.status_code, 200)

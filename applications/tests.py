from django.test import TestCase, Client
from django.core import mail
from django.contrib.auth import get_user_model
from companies.models import Company
from jobs.models import Job
from applications.models import Application
from applications.notifications import generate_offer_letter_pdf, send_application_notification
from recruiters.models import RecruiterProfile
from students.models import StudentProfile

User = get_user_model()


class EmailNotificationAndOfferLetterTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Tech Corp",
            location="Bangalore",
            industry="Software"
        )
        self.recruiter_user = User.objects.create_user(
            username="recruiter1",
            email="recruiter@example.com",
            password="password123",
            role=User.ROLE_RECRUITER
        )
        self.recruiter_profile = self.recruiter_user.recruiter_profile
        self.recruiter_profile.company = self.company
        self.recruiter_profile.save()

        self.student_user = User.objects.create_user(
            username="student1",
            email="student@example.com",
            password="password123",
            role=User.ROLE_STUDENT,
            first_name="Jane",
            last_name="Doe"
        )
        self.student_profile = self.student_user.student_profile
        self.student_profile.institution = "MIT"
        self.student_profile.degree = "B.Tech CS"
        self.student_profile.save()
        self.internship_job = Job.objects.create(
            recruiter=self.recruiter_user,
            company=self.company,
            title="Backend AI Intern",
            job_type=Job.JOB_TYPE_INTERNSHIP,
            work_mode=Job.WORK_MODE_REMOTE,
            description="Build cool things with AI",
            status=Job.STATUS_ACTIVE
        )
        self.fulltime_job = Job.objects.create(
            recruiter=self.recruiter_user,
            company=self.company,
            title="Senior Python Dev",
            job_type=Job.JOB_TYPE_FULL_TIME,
            work_mode=Job.WORK_MODE_REMOTE,
            description="Lead backend systems",
            status=Job.STATUS_ACTIVE
        )
        self.intern_app = Application.objects.create(
            job=self.internship_job,
            student=self.student_user,
            overall_match_score=92.5,
            status=Application.STATUS_APPLIED
        )

    def test_pdf_generation_returns_valid_pdf(self):
        """Test that reportlab generates a valid PDF with correct signature."""
        pdf_bytes = generate_offer_letter_pdf(self.intern_app)
        self.assertTrue(len(pdf_bytes) > 0)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))

    def test_status_notification_sends_email(self):
        """Test that changing status sends an email to the student."""
        mail.outbox.clear()
        sent = send_application_notification(
            self.intern_app,
            old_status='applied',
            new_status='shortlisted'
        )
        self.assertTrue(sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Shortlisted", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, [self.student_user.email])

    def test_duplicate_status_prevents_email(self):
        """Test that identical old and new status does not trigger an email."""
        mail.outbox.clear()
        sent = send_application_notification(
            self.intern_app,
            old_status='shortlisted',
            new_status='shortlisted'
        )
        self.assertFalse(sent)
        self.assertEqual(len(mail.outbox), 0)

    def test_offered_status_attaches_pdf_for_internship(self):
        """Test that offering an internship generates & attaches the offer letter PDF."""
        mail.outbox.clear()
        sent = send_application_notification(
            self.intern_app,
            old_status='interview',
            new_status='offered'
        )
        self.assertTrue(sent)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("Offer", email.subject)
        # Check attachment
        self.assertEqual(len(email.attachments), 1)
        filename, content, mimetype = email.attachments[0]
        self.assertEqual(filename, 'Internship_Offer_Letter.pdf')
        self.assertEqual(mimetype, 'application/pdf')
        self.assertTrue(content.startswith(b'%PDF-'))
        # Check that offer_letter_file was saved to model
        self.intern_app.refresh_from_db()
        self.assertTrue(bool(self.intern_app.offer_letter_file))
        self.assertIsNotNone(self.intern_app.offer_letter_sent_at)

    def test_recruiter_status_update_api_triggers_notification(self):
        """Test that the recruiter status update API triggers notification."""
        client = Client()
        client.force_login(self.recruiter_user)
        mail.outbox.clear()

        response = client.post(
            f'/recruiter/api/applications/{self.intern_app.pk}/status/',
            data='{"status": "interview"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['status_changed'])
        self.assertTrue(data['email_sent'])
        self.assertEqual(data['status'], 'interview')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Interview", mail.outbox[0].subject)

    def test_unchanged_status_does_not_trigger_notification(self):
        """Test that updating with the same status does not trigger an email notification."""
        client = Client()
        client.force_login(self.recruiter_user)
        mail.outbox.clear()

        response = client.post(
            f'/recruiter/api/applications/{self.intern_app.pk}/status/',
            data='{"status": "applied"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['status_changed'])
        self.assertFalse(data['email_sent'])
        self.assertEqual(len(mail.outbox), 0)

    def test_unauthorized_recruiter_cannot_update_another_companys_application(self):
        """Test that a recruiter from another company cannot update this application (company isolation)."""
        other_company = Company.objects.create(name="Competitor Inc", location="Mumbai")
        other_recruiter = User.objects.create_user(
            username="other_recruiter",
            email="other@competitor.com",
            password="password123",
            role=User.ROLE_RECRUITER
        )
        other_recruiter.recruiter_profile.company = other_company
        other_recruiter.recruiter_profile.save()

        client = Client()
        client.force_login(other_recruiter)
        mail.outbox.clear()

        response = client.post(
            f'/recruiter/api/applications/{self.intern_app.pk}/status/',
            data='{"status": "shortlisted"}',
            content_type='application/json'
        )
        # Must return 404 because job__recruiter != other_recruiter
        self.assertEqual(response.status_code, 404)
        self.intern_app.refresh_from_db()
        self.assertEqual(self.intern_app.status, Application.STATUS_APPLIED)
        self.assertEqual(len(mail.outbox), 0)

    def test_candidate_profile_view_ensures_csrf_cookie(self):
        """Test that recruiter candidate profile view sets the CSRF cookie."""
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.recruiter_user)

        response = client.get(
            f'/recruiter/candidates/{self.student_user.id}/?job_id={self.internship_job.id}'
        )
        self.assertEqual(response.status_code, 200)
        csrf_cookie = response.cookies.get('csrftoken')
        self.assertIsNotNone(csrf_cookie, "CSRF cookie must be set on candidate profile view")
        self.assertTrue(len(csrf_cookie.value) > 0)

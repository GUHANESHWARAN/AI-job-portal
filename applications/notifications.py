"""
applications/notifications.py

Professional notification engine for the AI Job & Internship Portal.

Responsibilities:
- Send status-change email notifications to students
- Generate PDF offer letters for internship offers (reportlab)
- Attach PDF to offer emails
- Auto-detect email backend (console vs SMTP)
- Prevent duplicate emails when status hasn't changed

Usage:
    from applications.notifications import send_application_notification
    send_application_notification(application, old_status='reviewing', new_status='shortlisted')
"""

import io
import logging
import os
from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# STATUS MESSAGE MAP
# ──────────────────────────────────────────────────────────────────────────────

STATUS_MESSAGES = {
    'applied': {
        'subject': '[Application Received] {job_title} at {company_name}',
        'message': (
            "Thank you for applying for <strong>{job_title}</strong> at <strong>{company_name}</strong>. "
            "Your application has been received and logged into our recruitment system."
        ),
        'next_steps': (
            "The hiring team will review your profile and AI compatibility score. "
            "You will be notified by email as soon as your application moves to the next stage."
        ),
    },
    'reviewing': {
        'subject': '[Under Review] {job_title} at {company_name}',
        'message': (
            "Your application for <strong>{job_title}</strong> at <strong>{company_name}</strong> "
            "is now under review by the recruitment team. We'll keep you updated as your application "
            "progresses through the pipeline."
        ),
        'next_steps': (
            "No action required from you at this time. You'll receive another update when a decision is made."
        ),
    },
    'shortlisted': {
        'subject': "[Shortlisted] Congratulations! You've been Shortlisted - {job_title} at {company_name}",
        'message': (
            "Excellent news! You have been <strong>shortlisted</strong> for the position of "
            "<strong>{job_title}</strong> at <strong>{company_name}</strong>. Your profile stood "
            "out among many strong candidates."
        ),
        'next_steps': (
            "Watch your email for the next communication from {company_name}. "
            "They may reach out to schedule an interview or assessment."
        ),
    },
    'interview': {
        'subject': "[Interview] Interview Scheduled - {job_title} at {company_name}",
        'message': (
            "An interview has been scheduled for your application to <strong>{job_title}</strong> "
            "at <strong>{company_name}</strong>. Please check the portal for details about the "
            "interview format, date, and time."
        ),
        'next_steps': (
            "Log in to the portal to view full interview details. "
            "Prepare well — review the job description and brush up on your skills. Best of luck!"
        ),
    },
    'selected': {
        'subject': "[Selected] You've Been Selected! - {job_title} at {company_name}",
        'message': (
            "Congratulations! You have been <strong>selected</strong> for the position of "
            "<strong>{job_title}</strong> at <strong>{company_name}</strong>. "
            "This is a major achievement — well done!"
        ),
        'next_steps': (
            "A formal offer letter will be sent shortly. "
            "Please log in to the portal to confirm your availability and readiness."
        ),
    },
    'offered': {
        'subject': "[Offer Letter] Offer Extended - {job_title} at {company_name}",
        'message': (
            "We are delighted to inform you that <strong>{company_name}</strong> has extended "
            "a formal offer for the position of <strong>{job_title}</strong>. "
            "Please find the official offer letter attached to this email."
        ),
        'next_steps': (
            "Please review the attached offer letter and respond on the portal "
            "by accepting or declining the offer. Contact the company directly for any questions."
        ),
    },
    'accepted': {
        'subject': "[Accepted] Welcome to {company_name} - {job_title}",
        'message': (
            "This confirms that your offer for <strong>{job_title}</strong> at "
            "<strong>{company_name}</strong> has been <strong>accepted</strong>. "
            "Welcome aboard — we wish you a great experience!"
        ),
        'next_steps': (
            "{company_name} will contact you soon with onboarding details and your joining date."
        ),
    },
    'rejected': {
        'subject': "[Update] Application Status Update - {job_title} at {company_name}",
        'message': (
            "Thank you for applying to <strong>{job_title}</strong> at <strong>{company_name}</strong>. "
            "After careful consideration, the team has decided to move forward with other candidates "
            "at this time. We encourage you to keep applying — many great opportunities await you."
        ),
        'next_steps': (
            "Don't be discouraged! Browse other open positions on the portal that match your profile. "
            "Your AI match score will help you find the best-fit opportunities."
        ),
    },
}


def _get_portal_url():
    """Return the portal base URL (configurable via SITE_URL setting)."""
    return getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')


def _format_work_mode(work_mode):
    labels = {
        'remote': 'Remote / Work From Home',
        'hybrid': 'Hybrid',
        'on_site': 'On-Site / Office',
    }
    return labels.get(work_mode, work_mode.replace('_', ' ').title())


# ──────────────────────────────────────────────────────────────────────────────
# PDF OFFER LETTER GENERATOR  (reportlab)
# ──────────────────────────────────────────────────────────────────────────────

def generate_offer_letter_pdf(application) -> bytes:
    """
    Generate a professional internship offer letter PDF using reportlab.
    Returns the PDF as bytes.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm, cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    except ImportError:
        logger.error("reportlab is not installed. Run: pip install reportlab")
        raise

    student = application.student
    job = application.job
    company = job.company

    student_name = student.get_full_name() or student.username
    job_title = job.title
    company_name = company.name
    company_location = company.location or 'India'
    offer_date = timezone.now().strftime('%d %B %Y')

    # --- Build PDF in memory ---
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Colors
    PRIMARY = colors.HexColor('#4F46E5')
    SECONDARY = colors.HexColor('#0EA5E9')
    DARK = colors.HexColor('#0F172A')
    MUTED = colors.HexColor('#64748B')
    LIGHT_BG = colors.HexColor('#EEF2FF')
    WHITE = colors.white

    styles = getSampleStyleSheet()

    style_company = ParagraphStyle(
        'company', fontName='Helvetica-Bold', fontSize=20,
        textColor=PRIMARY, spaceAfter=2, alignment=TA_CENTER
    )
    style_tagline = ParagraphStyle(
        'tagline', fontName='Helvetica', fontSize=10,
        textColor=MUTED, spaceAfter=4, alignment=TA_CENTER
    )
    style_doc_title = ParagraphStyle(
        'doc_title', fontName='Helvetica-Bold', fontSize=14,
        textColor=DARK, spaceAfter=4, alignment=TA_CENTER, spaceBefore=8
    )
    style_ref = ParagraphStyle(
        'ref', fontName='Helvetica', fontSize=9, textColor=MUTED,
        spaceAfter=12, alignment=TA_CENTER
    )
    style_body = ParagraphStyle(
        'body', fontName='Helvetica', fontSize=11, textColor=DARK,
        leading=18, spaceAfter=12, alignment=TA_JUSTIFY
    )
    style_bold = ParagraphStyle(
        'bold', fontName='Helvetica-Bold', fontSize=11, textColor=DARK,
        leading=18, spaceAfter=6
    )
    style_section = ParagraphStyle(
        'section', fontName='Helvetica-Bold', fontSize=11,
        textColor=PRIMARY, spaceBefore=14, spaceAfter=6
    )
    style_footer = ParagraphStyle(
        'footer', fontName='Helvetica', fontSize=9,
        textColor=MUTED, alignment=TA_CENTER, spaceBefore=20
    )
    style_signature_name = ParagraphStyle(
        'sig_name', fontName='Helvetica-Bold', fontSize=12, textColor=DARK
    )
    style_signature_title = ParagraphStyle(
        'sig_title', fontName='Helvetica', fontSize=10, textColor=MUTED
    )

    story = []

    # ── Header ──
    story.append(Paragraph(company_name, style_company))
    story.append(Paragraph(company_location, style_tagline))
    story.append(HRFlowable(width='100%', thickness=2, color=PRIMARY, spaceAfter=10))

    story.append(Paragraph('INTERNSHIP OFFER LETTER', style_doc_title))
    story.append(Paragraph(
        f'Ref: TB-{application.pk:05d} | Date: {offer_date}',
        style_ref
    ))

    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=16))

    # ── Candidate Details Table ──
    candidate_data = [
        ['Candidate Name', student_name],
        ['Email', student.email],
        ['Position', job_title],
        ['Company', company_name],
        ['Location', company_location],
        ['Work Mode', _format_work_mode(job.work_mode)],
        ['Offer Date', offer_date],
        ['AI Match Score', f"{application.overall_match_score:.1f}%"],
    ]

    detail_table = Table(candidate_data, colWidths=[5 * cm, None])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_BG),
        ('TEXTCOLOR', (0, 0), (0, -1), PRIMARY),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 16))

    # ── Salutation ──
    story.append(Paragraph(f'Dear {student_name},', style_bold))
    story.append(Spacer(1, 4))

    # ── Opening ──
    story.append(Paragraph(
        f'We are delighted to offer you an internship position at <b>{company_name}</b> as a '
        f'<b>{job_title}</b>. This offer has been made following a thorough evaluation of your '
        f'profile, skills, and AI compatibility score of <b>{application.overall_match_score:.1f}%</b> '
        f'against our role requirements.',
        style_body
    ))

    story.append(Paragraph(
        f'Your selection from a competitive pool of candidates reflects the high regard we have for '
        f'your abilities. We believe this internship will provide you with valuable industry experience '
        f'while you contribute meaningfully to our team.',
        style_body
    ))

    # ── Role & Responsibilities ──
    story.append(Paragraph('Role & Responsibilities', style_section))
    responsibilities = job.responsibilities or (
        "You will work closely with the core team to contribute to project goals, "
        "gain hands-on experience, and develop professional skills aligned with "
        "the requirements of the role."
    )
    story.append(Paragraph(responsibilities[:500] + ('...' if len(responsibilities) > 500 else ''), style_body))

    # ── Terms ──
    story.append(Paragraph('Terms & Conditions', style_section))
    story.append(Paragraph(
        '1. This offer is contingent upon completion of document verification and background screening.',
        style_body
    ))
    story.append(Paragraph(
        '2. You are required to maintain confidentiality of all proprietary information encountered '
        'during the course of your internship.',
        style_body
    ))
    story.append(Paragraph(
        '3. This offer is non-transferable and valid only for the candidate named herein.',
        style_body
    ))

    # ── Acceptance ──
    story.append(Paragraph('Acceptance of Offer', style_section))
    story.append(Paragraph(
        'Please confirm your acceptance of this offer by logging into the TalentBridge AI portal '
        'and clicking <b>"Accept Offer"</b> on your application. '
        'Should you have any questions, do not hesitate to reach out.',
        style_body
    ))

    # ── Closing ──
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f'We look forward to welcoming you to the {company_name} family. '
        f'Congratulations once again, and best of luck in your career journey!',
        style_body
    ))

    story.append(Spacer(1, 24))

    # ── Signature Block ──
    sig_data = [
        [Paragraph('For TalentBridge AI Platform', style_signature_title), ''],
        [Paragraph('Authorised Signatory', style_signature_name), ''],
        [Paragraph('Recruitment Team', style_signature_title), ''],
        [Paragraph(offer_date, style_signature_title), Paragraph(
            f'Ref: TB-{application.pk:05d}',
            ParagraphStyle('ref_right', fontName='Helvetica', fontSize=9,
                           textColor=MUTED, alignment=TA_LEFT)
        )],
    ]
    sig_table = Table(sig_data, colWidths=[None, None])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)

    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceBefore=20))

    # ── Footer ──
    story.append(Paragraph(
        f'This document was generated by TalentBridge AI on {offer_date}. '
        f'Document ID: TB-OL-{application.pk:05d} | This is an official offer letter.',
        style_footer
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def _save_offer_letter_pdf(application, pdf_bytes: bytes) -> str:
    """Save PDF to media/offer_letters/<app_id>/ and return the relative path."""
    from django.core.files.base import ContentFile

    filename = f'offer_letters/app_{application.pk}/internship_offer_letter.pdf'
    application.offer_letter_file.save(
        f'internship_offer_letter.pdf',
        ContentFile(pdf_bytes),
        save=False
    )
    return application.offer_letter_file.name


# ──────────────────────────────────────────────────────────────────────────────
# MAIN NOTIFICATION FUNCTION
# ──────────────────────────────────────────────────────────────────────────────

def send_application_notification(application, old_status: str, new_status: str) -> bool:
    """
    Send email notification to student when application status changes.

    - Does NOT send if old_status == new_status (prevents duplicates).
    - For STATUS_OFFERED internships: generates PDF offer letter + attaches to email.
    - Logs errors instead of raising, so the main request is never blocked.

    Returns True if email was sent successfully, False otherwise.
    """
    # Guard: no-op if status didn't actually change
    if old_status == new_status:
        return False

    # Guard: only notify for statuses that have a message configured
    template_data = STATUS_MESSAGES.get(new_status)
    if not template_data:
        return False

    student = application.student
    student_email = student.email
    if not student_email:
        logger.warning(
            f"Application {application.pk}: student {student.username} has no email — skipping notification."
        )
        return False

    job = application.job
    company = job.company

    student_name = student.get_full_name() or student.username
    job_title = job.title
    company_name = company.name
    job_location = job.location or company.location or 'India'
    job_type = job.get_job_type_display()
    work_mode = _format_work_mode(job.work_mode)
    portal_url = _get_portal_url()
    updated_at = timezone.now().strftime('%d %B %Y, %I:%M %p IST')
    offer_date = timezone.now().strftime('%d %B %Y')
    status_display = dict(application.STATUS_CHOICES).get(new_status, new_status.title())

    fmt = dict(
        student_name=student_name,
        job_title=job_title,
        company_name=company_name,
        job_location=job_location,
    )

    subject = template_data['subject'].format(**fmt)
    html_message_body = template_data['message'].format(**fmt)
    next_steps = template_data['next_steps'].format(**fmt)

    # Decide template — offered internship gets dedicated template
    is_offer = (new_status == 'offered' and application.is_internship)

    template_name = 'emails/offer_letter_email.html' if is_offer else 'emails/status_notification.html'

    context = {
        'student_name': student_name,
        'job_title': job_title,
        'company_name': company_name,
        'job_location': job_location,
        'job_type': job_type,
        'work_mode': work_mode,
        'status': new_status,
        'status_display': status_display,
        'message': html_message_body,
        'next_steps': next_steps,
        'portal_url': portal_url,
        'updated_at': updated_at,
        'offer_date': offer_date,
    }

    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'TalentBridge AI <noreply@talentbridge.ai>')

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[student_email],
    )
    email.attach_alternative(html_content, 'text/html')

    # ── Generate & attach PDF offer letter for internship offers ──
    if is_offer:
        try:
            pdf_bytes = generate_offer_letter_pdf(application)
            _save_offer_letter_pdf(application, pdf_bytes)
            application.offer_letter_sent_at = timezone.now()
            application.save(update_fields=['offer_letter_file', 'offer_letter_sent_at'])
            email.attach(
                filename='Internship_Offer_Letter.pdf',
                content=pdf_bytes,
                mimetype='application/pdf'
            )
            logger.info(f"Application {application.pk}: offer letter PDF generated and attached.")
        except Exception as exc:
            logger.error(f"Application {application.pk}: PDF generation failed — {exc}")
            # Continue — still send the email without the PDF rather than blocking

    # ── Send ──
    try:
        email.send(fail_silently=False)
        logger.info(
            f"Application {application.pk}: status notification sent to {student_email} "
            f"({old_status} → {new_status})"
        )
        return True
    except Exception as exc:
        logger.error(
            f"Application {application.pk}: failed to send notification to {student_email} — {exc}"
        )
        return False


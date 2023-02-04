from celery import shared_task

from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_email(email_subject: str, email_body: str, to_whom: str):
    return send_mail(
        subject=email_subject, message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[to_whom])

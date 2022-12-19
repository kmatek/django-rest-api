from celery import shared_task

from anymail.message import AnymailMessage


@shared_task
def send_email(email_subject: str, email_body: str, to_whom: str):
    return AnymailMessage(
        subject=email_subject, body=email_body, to=[to_whom]).send()

from django.test import TestCase, override_settings
from django.core import mail

from ..utils import EmailSender

from .test_models import sample_user


@override_settings(
    EMAIL_BACKEND='anymail.backends.test.EmailBackend',
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True
)
class UtilsTests(TestCase):
    def test_send_email_with_sender(self):
        user = sample_user(
            email='test@email.com', name='Testname',
            password='TestPassword123!')
        sender = EmailSender(user)
        result = sender.send_email(title='test', message='test')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])
        self.assertTrue(result.successful())

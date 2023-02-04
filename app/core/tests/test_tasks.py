from django.test import TestCase, override_settings
from django.core import mail

from ..tasks import send_email


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True
)
class CeleryTasksTest(TestCase):
    def test_send_mail_task(self):
        result = send_email.delay(
            'test subject', 'test message', 'test@test.com')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@test.com'])
        self.assertTrue(result.successful())

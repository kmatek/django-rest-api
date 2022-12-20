from django.test import TestCase, override_settings
from django.core import mail

from core.tests.test_models import sample_user


@override_settings(
    EMAIL_BACKEND='anymail.backends.test.EmailBackend',
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True
)
class SignalsTests(TestCase):

    def test_send_activation_email_signal_work(self):
        """Check that signal send activation email"""
        sample_user(
            email='test@email.com', name='testname',
            password='TestPassword!123')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@email.com'])

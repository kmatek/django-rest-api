from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core import mail

from ..utils import EmailSender

from .test_models import sample_user


@override_settings(
    SUSPEND_SIGNALS=True,
    EMAIL_BACKEND='anymail.backends.test.EmailBackend',
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True
)
class UtilsTests(TestCase):
    def setUp(self):
        self.user = sample_user(
            email='test@email.com', name='Testname',
            password='TestPassword123!')

    def test_send_email_with_sender(self):
        sender = EmailSender(self.user)
        result = sender.send_email(title='test', message='test')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertTrue(result.successful())

    @patch('core.utils.EmailSender.make_message')
    def test_make_url(self, mock_message):
        sender = EmailSender(self.user)
        test_message = 'test_message'
        mock_message.return_value = test_message
        message = sender.make_message()

        self.assertEqual(message, test_message)

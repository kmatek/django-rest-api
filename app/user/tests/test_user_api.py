import os
import shutil
import tempfile

from PIL import Image

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import smart_bytes
from django.utils.http import urlsafe_base64_encode

from core.tests.test_models import sample_user

from rest_framework.test import APITestCase
from rest_framework import status


CREATE_USER_URL = reverse('user:create-user')
DETAIL_USER_URL = reverse('user:detail-user')
UPLOAD_USER_IMAGE_URL = reverse('user:upload-image-user')
CHANGE_PASSWORD_URL = reverse('user:change-user-password')
RESET_PASSWORD_URL = reverse('user:reset-password')
RESET_PASSWORD_CONFIRM_URL = reverse('user:reset-password-confirm')


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }
    },
)
class PublicUserAPITests(APITestCase):
    def test_create_user_with_valid_credentials(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': 'Testpassword!'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
        self.assertNotIn('activation_uuid', res.data)
        self.assertFalse(user.is_active)

    def test_user_exists(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': 'testpassword'
        }

        sample_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_view_not_allowed_method(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': 'testpassword'
        }

        res = self.client.get(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.put(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.patch(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.delete(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_password_is_too_short(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': '1234'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            res.data['password'][0],
            "Ensure this field has at least 8 characters.")

        self.assertFalse(
            get_user_model().objects.filter(
                email=payload['email']).exists())

    def test_password_does_not_contain_special_char(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': 'Testpassword'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            res.data['password'][0],
            "This password must contain at least 1 symbol:" +
            " ()[]{}|\\`~!@#$%^&*_-+=;:'\",<>./?")

        self.assertFalse(
            get_user_model().objects.filter(
                email=payload['email']).exists())

    def test_password_does_not_contain_uppercase_char(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': 'testpassword!'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            res.data['password'][0],
            "This password must contain at least 1 uppercase letter, A-Z.")

        self.assertFalse(
            get_user_model().objects.filter(
                email=payload['email']).exists())

    def test_password_does_not_contain_lowercase_char(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': 'TESTPASSWORD!'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            res.data['password'][0],
            "This password must contain at least 1 lowercase letter, a-z.")

        self.assertFalse(
            get_user_model().objects.filter(
                email=payload['email']).exists())

    def test_password_is_entirely_numeric(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': '12345678'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            res.data['password'][1],
            "This password is entirely numeric.",)

        self.assertFalse(
            get_user_model().objects.filter(
                email=payload['email']).exists())

    def test_name_is_too_short(self):
        payload = {
            'email': 'test@email.com',
            'name': '1234',
            'password': 'testpassword'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(
            get_user_model().objects.filter(
                email=payload['email']).exists())

    def test_user_with_this_name_exist(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': 'testpassword'
        }

        sample_user(**payload)

        payload.update(
            {
                'email': 'test@email2.com',
                'password': 'TestPassword!123'
            })

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_name_contains_special_char(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname!213',
            'password': 'testpassword'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(
            get_user_model().objects.filter(
                email=payload['email']).exists())

    def test_upload_image_unauthorized(self):
        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            img = Image.new('RGB', (200, 200))
            img.save(image_file, 'png')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.put(UPLOAD_USER_IMAGE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrievie_user_detail_unauthorized(self):
        res = self.client.get(DETAIL_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_unauthorized(self):
        payload = {
            'password': 'testpassword',
            'new_password': 'Newpassword!123'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(
        EMAIL_BACKEND='anymail.backends.test.EmailBackend',
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True
    )
    def test_reset_password_with_valid_credentials(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': 'Testpassword!'
        }

        sample_user(**payload)

        res = self.client.post(RESET_PASSWORD_URL, {'email': payload['email']})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [(payload['email'])])

    def test_reset_password_with_invalid_credentials(self):
        payload = {'email': 'test@email.com'}

        res = self.client.post(RESET_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_not_allowed_methods(self):
        payload = {'email': ''}

        res = self.client.get(RESET_PASSWORD_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.put(RESET_PASSWORD_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.patch(RESET_PASSWORD_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.delete(RESET_PASSWORD_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_reset_password_confirm_with_valid_credenatials(self):
        user = sample_user(
            email='test@email.com', name='testname',
            password='TestPassword1!@#')

        # Check old user password.
        self.assertTrue(user.check_password('TestPassword1!@#'))

        encoded_user_id = urlsafe_base64_encode(smart_bytes(user.id))
        token = default_token_generator.make_token(user)
        payload = {
            'user_id': encoded_user_id,
            'token': token,
            'new_password': 'Testpassword123@'
        }

        res = self.client.post(RESET_PASSWORD_CONFIRM_URL, payload)
        user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(user.check_password('TestPassword1!@#'))
        self.assertTrue(user.check_password('Testpassword123@'))
        self.assertNotIn('new_password', res.data)
        self.assertNotIn('user_id', res.data)
        self.assertNotIn('token', res.data)

    def test_reset_password_confirm_with_expired_token(self):
        user = sample_user(
            email='test@email.com', name='testname',
            password='TestPassword1!@#')
        encoded_user_id = urlsafe_base64_encode(smart_bytes(user.id))
        token = default_token_generator.make_token(user)
        # Change user password to make token expired.
        user.set_password('TestPassword123!@#')
        user.save()
        payload = {
            'user_id': encoded_user_id,
            'token': token,
            'new_password': 'Testpassword123@'
        }
        res = self.client.post(RESET_PASSWORD_CONFIRM_URL, payload)
        user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # Check old user password.
        self.assertTrue(user.check_password('TestPassword123!@#'))
        self.assertFalse(user.check_password('TestPassword123@'))
        self.assertNotIn('new_password', res.data)
        self.assertNotIn('user_id', res.data)
        self.assertIn('token', res.data)
        self.assertEqual(res.data['token'][0].code, 'invalid')

    def test_reset_password_confirm_with_wrong_same_password(self):
        user = sample_user(
            email='test@email.com', name='testname',
            password='TestPassword1!@#')
        encoded_user_id = urlsafe_base64_encode(smart_bytes(user.id))
        token = default_token_generator.make_token(user)
        payload = {
            'user_id': encoded_user_id,
            'token': token,
            'new_password': 'TestPassword1!@#'
        }
        res = self.client.post(RESET_PASSWORD_CONFIRM_URL, payload)
        user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('user_id', res.data)
        self.assertNotIn('token', res.data)
        self.assertIn('new_password', res.data)
        self.assertEqual(
            res.data['new_password'][0],
            'The new password is similar to the old one.')

    def test_reset_password_confirm_with_invalid_password(self):
        user = sample_user(
            email='test@email.com', name='testname',
            password='TestPassword1!@#')
        encoded_user_id = urlsafe_base64_encode(smart_bytes(user.id))
        token = default_token_generator.make_token(user)
        payload = {
            'user_id': encoded_user_id,
            'token': token,
            'new_password': '1234567'
        }
        res = self.client.post(RESET_PASSWORD_CONFIRM_URL, payload)
        user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # Check old user password.
        self.assertTrue(user.check_password('TestPassword1!@#'))
        self.assertFalse(user.check_password('1234567'))
        self.assertNotIn('user_id', res.data)
        self.assertNotIn('token', res.data)
        self.assertIn('new_password', res.data)
        self.assertEqual(res.data['new_password'][0].code, "min_length")


class AuthenticatedUserAPITests(APITestCase):

    def setUp(self):
        self.user = sample_user(
            email='test@email.com', name='test', password='testpassword')
        self.client.force_authenticate(user=self.user)

    def test_retrieve_users_detail(self):
        res = self.client.get(DETAIL_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name,
            'image': None,
            'is_active': False
        })

    def test_retrieve_users_not_allowed_methods(self):
        res = self.client.post(DETAIL_USER_URL)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.put(DETAIL_USER_URL)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.patch(DETAIL_USER_URL)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.delete(DETAIL_USER_URL)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_change_password_correct(self):
        payload = {
            'password': 'testpassword',
            'new_password': 'Newpassword!123'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn('password' or 'new_password', res.data)
        self.assertTrue(self.user.check_password(payload['new_password']))

    def test_change_password_with_similar_passwords(self):
        payload = {
            'password': 'testpassword',
            'new_password': 'testpassword'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('password' or 'new_password', res.data)

    def test_change_password_with_wrong_old_password(self):
        payload = {
            'password': 'wrongone',
            'new_password': 'newpassword'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(payload['password']))
        self.assertFalse(self.user.check_password(payload['new_password']))

    def test_change_password_not_allowed_methods(self):
        payload = {
            'password': 'wrongone',
            'new_password': 'newpassword'
        }

        res = self.client.get(CHANGE_PASSWORD_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.post(CHANGE_PASSWORD_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.delete(CHANGE_PASSWORD_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_change_password_does_not_contain_special_char(self):
        payload = {
            'password': 'testpassword',
            'new_password': 'Newpassword12'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('password' or 'new_password', res.data)
        self.assertFalse(self.user.check_password(payload['new_password']))
        self.assertEqual(
            res.data['new_password'][0],
            "This password must contain at least 1 symbol:" +
            " ()[]{}|\\`~!@#$%^&*_-+=;:'\",<>./?")

    def test_change_password_does_not_contain_uppercase_char(self):
        payload = {
            'password': 'testpassword',
            'new_password': '!newpassword12'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('password' or 'new_password', res.data)
        self.assertFalse(self.user.check_password(payload['new_password']))
        self.assertEqual(
            res.data['new_password'][0],
            "This password must contain at least 1 uppercase letter, A-Z.")

    def test_change_password_does_not_contain_lowercase_char(self):
        payload = {
            'password': 'testpassword',
            'new_password': '!NEWPASSWORD12'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('password' or 'new_password', res.data)
        self.assertFalse(self.user.check_password(payload['new_password']))
        self.assertEqual(
            res.data['new_password'][0],
            "This password must contain at least 1 lowercase letter, a-z.")

    def test_change_password_is_entirely_numeric(self):
        payload = {
            'password': 'testpassword',
            'new_password': '123456789'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('password' or 'new_password', res.data)
        self.assertFalse(self.user.check_password(payload['new_password']))
        self.assertEqual(
            res.data['new_password'][1],
            "This password is entirely numeric.",)


class UserImageUploadTests(APITestCase):

    def setUp(self):
        self.user = sample_user(
            email='test@email.com', name='test', password='testpassword')
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.user.image.delete()
        path = '/vol/web/media/uploads/albums/test@email.com'
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_upload_user_image(self):
        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            img = Image.new('RGB', (200, 200))
            img.save(image_file, 'png')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.put(UPLOAD_USER_IMAGE_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.user.image.path))

    def test_upload_image_bigger_than_1MB(self):
        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            img = Image.new('RGB', (200, 200))
            img.save(image_file, 'png')
            image_file.seek(1048576+1)
            payload = {'image': image_file}
            res = self.client.put(UPLOAD_USER_IMAGE_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.image)

    def test_uploaded_wrong_dimensions_image(self):
        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            img = Image.new('RGB', (100, 100))
            img.save(image_file, 'png')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.put(UPLOAD_USER_IMAGE_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.image)

    def test_upload_gif_extension(self):
        with tempfile.NamedTemporaryFile(suffix='.gif') as image_file:
            img = Image.new('RGB', (200, 200))
            img.save(image_file, 'gif')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.put(UPLOAD_USER_IMAGE_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.image)


TESTING_THRESHOLD = '5/min'


@override_settings(
    EMAIL_BACKEND='anymail.backends.test.EmailBackend',
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    THROTTLE_THRESHOLD=TESTING_THRESHOLD,
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': '/var/tmp/django_cache',
        }
    },
)
class TestThrottling(APITestCase):
    def tearDown(self):
        path = '/var/tmp/django_cache'
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_password_reset_throttling(self):
        payload = {
            'email': 'test@email.com',
            'name': 'testname',
            'password': 'Testpassword!'
        }
        sample_user(**payload)
        for i in range(0, 5):
            self.client.post(RESET_PASSWORD_URL, payload)
        response = self.client.post(RESET_PASSWORD_URL, payload)
        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS)

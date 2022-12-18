import os
import shutil
import tempfile

from PIL import Image

from django.urls import reverse
from django.contrib.auth import get_user_model

from core.tests.test_models import sample_user

from rest_framework.test import APITestCase
from rest_framework import status


CREATE_USER_URL = reverse('user:create-user')
DETAIL_USER_URL = reverse('user:detail-user')
UPLOAD_USER_IMAGE_URL = reverse('user:upload-image-user')
CHANGE_PASSWORD_URL = reverse('user:change-user-password')


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

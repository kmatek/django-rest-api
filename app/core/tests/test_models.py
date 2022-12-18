from unittest.mock import patch
import os
import shutil
import tempfile

from PIL import Image

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from core import models


def sample_user(**params):
    return get_user_model().objects.create_user(**params)


def sample_superuser(**params):
    return get_user_model().objects.create_superuser(**params)


class ModelTests(TestCase):

    def tearDown(self):
        path = '/vol/web/media/uploads/albums/test@email.com'
        if os.path.exists(path):
            shutil.rmtree(path)
        path = '/vol/web/media/uploads/profile_pics/test@email.com'
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_create_user_with_correct_email(self):
        params = {
            'email': 'test@email.com',
            'name': 'test',
            'password': 'testpassword'
        }

        user = sample_user(**params)

        for key in params.keys():
            if key == 'password':
                self.assertTrue(user.check_password(params[key]))
                continue
            self.assertEqual(getattr(user, key), params[key])

        self.assertFalse(user.is_active)

    def test_create_user_with_invalid_email(self):
        with self.assertRaises(ValueError):
            params = {
                'email': None,
                'name': 'test',
                'password': 'testpassword'
            }

            sample_user(**params)

    def test_create_user_with_invalid_name(self):
        with self.assertRaises(ValueError):
            params = {
                'email': 'test@email.com',
                'name': None,
                'password': 'testpassword'
            }

            sample_user(**params)

    def test_normalize_email(self):
        params = {
            'email': 'test@EMAIL.com',
            'name': 'test',
            'password': 'testpassword'
        }

        user = sample_user(**params)

        self.assertEqual(user.email, params['email'].lower())

    def test_normalize_name(self):
        params = {
            'email': 'test@email.com',
            'name': 'TESTNAME',
            'password': 'testpassword'
        }

        user = sample_user(**params)

        self.assertEqual(user.name, params['name'].lower())

    def test_create_superuser(self):
        params = {
            'email': 'admin@email.com',
            'name': 'admin',
            'password': 'adminpassword'
        }

        super_user = sample_superuser(**params)

        self.assertTrue(super_user.is_staff)
        self.assertTrue(super_user.is_superuser)

    @patch('core.models.uuid.uuid4')
    def test_user_image_file_path(self, mock_uuid):
        user = sample_user(
            name='testname',
            email='test@email.com',
            password='testPassword!123'
        )
        uuid = 'testing-uuid'
        mock_uuid.return_value = uuid
        file_path = models.user_image_file_path(user, 'test.jpg')

        self.assertEqual(
            file_path,
            f'uploads/profile_pics/{user.email}/{uuid}.jpg'
        )

    @patch('core.models.uuid.uuid4')
    def test_user_image(self, mock_uuid):
        user = sample_user(
            name='testname',
            email='test@email.com',
            password='testPassword!123'
        )
        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            img = Image.new('RGB', (1, 1))
            img.save(image_file, 'png')
            image_file.seek(1*1024*1024+1)

            image = InMemoryUploadedFile(
                image_file,
                'image',
                'image.png',
                'png',
                image_file.tell(),
                None
            )
            user.image = image
            user.save()
            uuid = 'testing-uuid'
            mock_uuid.return_value = uuid
            file_path = models.user_image_file_path(user, image.name)

            self.assertEqual(
                file_path,
                f'uploads/profile_pics/{user.email}/{uuid}.png'
            )
            self.assertTrue(user.image)

    def test_user_image_with_wrong_size(self):
        user = sample_user(
            name='testname',
            email='test@email.com',
            password='testPassword!123'
        )
        with self.assertRaises(ValidationError):
            with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
                img = Image.new('RGB', (1, 1))
                img.save(image_file, 'png')
                image_file.seek(1*1024*1024+1)

                image = InMemoryUploadedFile(
                    image_file,
                    'image',
                    'image.png',
                    'png',
                    image_file.tell(),
                    None
                )
                user.image = image
                user.full_clean()

    def test_user_image_with_wrong_ext(self):
        user = sample_user(
            name='testname',
            email='test@email.com',
            password='testPassword!123'
        )
        with self.assertRaises(ValidationError):
            with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
                img = Image.new('RGB', (1, 1))
                img.save(image_file, 'png')
                image_file.seek(1)

                image = InMemoryUploadedFile(
                    image_file,
                    'image',
                    'image.gif',
                    'gif',
                    image_file.tell(),
                    None
                )
                user.image = image
                user.full_clean()

    def test_user_image_with_wrong_dimensions(self):
        user = sample_user(
            name='testname',
            email='test@email.com',
            password='testPassword!123'
        )
        with self.assertRaises(ValidationError):
            with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
                img = Image.new('RGB', (199, 199))
                img.save(image_file, 'png')
                image_file.seek(1)

                image = InMemoryUploadedFile(
                    image_file,
                    'image',
                    'image.png',
                    'png',
                    image_file.tell(),
                    None
                )
                user.image = image
                user.full_clean()

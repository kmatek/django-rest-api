from unittest.mock import patch
import os
import shutil
import tempfile

from PIL import Image

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from core import models


def sample_user(**params):
    return get_user_model().objects.create_user(**params)


def sample_superuser(**params):
    return get_user_model().objects.create_superuser(**params)


def sample_album(**params):
    return models.Album.objects.create(**params)


def sample_album_photo(**params):
    return models.AlbumPhoto.objects.create(**params)


def sample_album_like(**params):
    return models.AlbumLike.objects.create(**params)


@override_settings(SUSPEND_SIGNALS=True)
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
            name='testname', email='test@email.com',
            password='testPassword!123')
        uuid = 'testing-uuid'
        mock_uuid.return_value = uuid
        file_path = models.user_image_file_path(user, 'test.jpg')

        self.assertEqual(
            file_path, f'uploads/profile_pics/{user.email}/{uuid}.jpg')

    @patch('core.models.uuid.uuid4')
    def test_user_image(self, mock_uuid):
        user = sample_user(
            name='testname', email='test@email.com',
            password='testPassword!123')
        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            img = Image.new('RGB', (1, 1))
            img.save(image_file, 'png')
            image_file.seek(1*1024*1024+1)
            image = InMemoryUploadedFile(
                image_file, 'image', 'image.png',
                'png', image_file.tell(), None)
            user.image = image
            user.save()
            uuid = 'testing-uuid'
            mock_uuid.return_value = uuid
            file_path = models.user_image_file_path(user, image.name)

            self.assertEqual(
                file_path, f'uploads/profile_pics/{user.email}/{uuid}.png')
            self.assertTrue(user.image)

    def test_user_image_with_wrong_size(self):
        user = sample_user(
            name='testname', email='test@email.com',
            password='testPassword!123')
        with self.assertRaises(ValidationError):
            with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
                img = Image.new('RGB', (1, 1))
                img.save(image_file, 'png')
                image_file.seek(1*1024*1024+1)
                image = InMemoryUploadedFile(
                    image_file, 'image', 'image.png',
                    'png', image_file.tell(), None)
                user.image = image
                user.full_clean()

    def test_user_image_with_wrong_ext(self):
        user = sample_user(
            name='testname', email='test@email.com',
            password='testPassword!123')
        with self.assertRaises(ValidationError):
            with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
                img = Image.new('RGB', (1, 1))
                img.save(image_file, 'png')
                image_file.seek(1)
                image = InMemoryUploadedFile(
                    image_file, 'image', 'image.gif',
                    'gif', image_file.tell(), None)
                user.image = image
                user.full_clean()

    def test_user_image_with_wrong_dimensions(self):
        user = sample_user(
            name='testname', email='test@email.com',
            password='testPassword!123')
        with self.assertRaises(ValidationError):
            with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
                img = Image.new('RGB', (199, 199))
                img.save(image_file, 'png')
                image_file.seek(1)
                image = InMemoryUploadedFile(
                    image_file, 'image', 'image.png',
                    'png', image_file.tell(), None)
                user.image = image
                user.full_clean()

    @patch('core.models.uuid.uuid4')
    def test_albumphoto_file_path(self, mock_uuid):
        user = sample_user(
            name='testname', email='test@email.com',
            password='testPassword!123')
        album = sample_album(owner=user, title='testtitle')

        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            img = Image.new('RGB', (200, 200))
            img.save(image_file, 'png')
            image_file.seek(0)
            image = InMemoryUploadedFile(
                image_file, 'image', 'image.png',
                'png', image_file.tell(), None)
            photo = sample_album_photo(album=album, image=image)

        uuid = 'testing-uuid'
        mock_uuid.return_value = uuid
        file_path = models.album_photo_file_path(photo, image_file.name)

        self.assertEqual(
            file_path, f'uploads/albums/{user.email}/{uuid}.png')

    @patch('core.models.uuid.uuid4')
    def test_albumphoto_model(self, mock_uuid):
        user = sample_user(
            name='testname', email='test@email.com',
            password='testPassword!123')
        album = sample_album(owner=user, title='testtitle')

        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            img = Image.new('RGB', (1, 1))
            img.save(image_file, 'png')
            image_file.seek(1)
            image = InMemoryUploadedFile(
                image_file, 'image', 'image.png',
                'png', image_file.tell(), None)
            photo = sample_album_photo(album=album, image=image)
            uuid = 'testing-uuid'
            mock_uuid.return_value = uuid
            file_path = models.album_photo_file_path(photo, image.name)

            self.assertEqual(
                file_path, f'uploads/albums/{user.email}/{uuid}.png')
            self.assertTrue(photo.image)

    def test_albumphoto_model_with_wrong_size(self):
        user = sample_user(
            name='testname', email='test@email.com',
            password='testPassword!123')
        album = sample_album(owner=user, title='testtitle')
        with self.assertRaises(ValidationError):
            with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
                img = Image.new('RGB', (1, 1))
                img.save(image_file, 'png')
                image_file.seek(1*1024*1024+1)

                image = InMemoryUploadedFile(
                    image_file, 'image', 'image.png',
                    'png', image_file.tell(), None)
                photo = models.AlbumPhoto(album=album, image=image)
                photo.full_clean()

    def test_albumphoto_model_with_wrong_ext(self):
        user = sample_user(
            name='testname', email='test@email.com',
            password='testPassword!123')
        album = sample_album(owner=user, title='testtitle')
        with self.assertRaises(ValidationError):
            with tempfile.NamedTemporaryFile(suffix='.gif') as image_file:
                img = Image.new('RGB', (1, 1))
                img.save(image_file, 'gif')
                image_file.seek(1)

                image = InMemoryUploadedFile(
                    image_file, 'image', 'image.gif',
                    'gif', image_file.tell(), None)
                photo = models.AlbumPhoto(album=album, image=image)
                photo.full_clean()

    def test_album_model(self):
        user = sample_user(
            name='testname', email='test@email.com',
            password='testPassword!123')
        params = {
            'title': 'testalbumtitle',
            'owner': user,
        }
        album = sample_album(**params)

        for key in params.keys():
            self.assertEqual(getattr(album, key), params[key])

        self.assertEqual(album.created_date.day, timezone.now().day)
        self.assertEqual(album.created_date.month, timezone.now().month)
        self.assertEqual(album.created_date.year, timezone.now().year)

    def test_album_like_model(self):
        users = (
            sample_user(
                name=f'testname{i}', email=f'test{i}@email.com',
                password='testPassword!123')
            for i in range(3)
        )

        album = sample_album(owner=next(users), title='test')

        for user in users:
            sample_album_like(album=album, user_liked=user)

        self.assertEqual(album.likes.count(), 2)

    @patch('core.models.uuid.uuid4')
    def test_removing_folder_after_deleting_user(self, mock_uuid):
        """Test of folder deletion after user deletion."""
        user = sample_user(
            name='testname', email='test@email.com',
            password='testPassword!123')
        album = sample_album(owner=user, title='testtitle')

        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            img = Image.new('RGB', (1, 1))
            img.save(image_file, 'png')
            image_file.seek(1)
            image = InMemoryUploadedFile(
                image_file, 'image', 'image.png',
                'png', image_file.tell(), None)
            photo = sample_album_photo(album=album, image=image)
            uuid = 'testing-uuid'
            mock_uuid.return_value = uuid
            file_path = models.album_photo_file_path(photo, image.name)

            self.assertEqual(
                file_path, f'uploads/albums/{user.email}/{uuid}.png')
            self.assertTrue(photo.image)

            user.delete()
            self.assertFalse(os._exists(file_path))

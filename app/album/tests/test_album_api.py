from rest_framework.test import APITestCase
from rest_framework import status

from django.test import override_settings
from django.urls import reverse

from core.tests.test_models import sample_user, sample_album
from core.models import Album
from album.serializers import AlbumSerializer, AlbumDetailSerializer

ALBUM_LIST_URL = reverse('album:album-list')


def get_detail_album_url(pk):
    return reverse('album:album-detail', args=[pk])


def like_album_url(pk):
    return reverse('album:album-like-album', args=[pk])


@override_settings(
    SUSPEND_SIGNALS=True,
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }
    },
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True
)
class AlbumViewSetTests(APITestCase):

    def setUp(self):
        self.user = sample_user(
            email='test@email.com', name='testname',
            password='TestPassword!123')
        self.album = sample_album(owner=self.user, title='images_album')

    def test_retrieve_album_list(self):
        sample_album(owner=self.user, title='testalbum')
        sample_album(owner=self.user, title='testalbum2')
        res = self.client.get(ALBUM_LIST_URL)
        serializer = AlbumSerializer(
            Album.objects.all().order_by('-id'),
            many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], serializer.data)

    def test_retrieve_album_retreive(self):
        album = sample_album(owner=self.user, title='testalbum')
        url = get_detail_album_url(album.id)
        serializer = AlbumDetailSerializer(album)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], serializer.data['id'])

    def test_album_create_unauthenticated(self):
        payload = {
            'title': 'testalbumtitle'
        }

        res = self.client.post(ALBUM_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_album_create_authenticated(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            'title': 'testalbumtitle'
        }

        res = self.client.post(ALBUM_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['owner'], self.user.email)

    def test_create_too_many_albums(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            'title': 'testalbumtitle'
        }

        for i in range(3):
            self.client.post(ALBUM_LIST_URL, payload)

        res = self.client.post(ALBUM_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_album_permission(self):
        self.client.force_authenticate(user=self.user)
        sample_album(owner=self.user, title='testalbum1')
        user2 = sample_user(
            email='test2@email.com', name='test2name',
            password='Testpassword!123')
        album2 = sample_album(owner=user2, title='testalbum2')

        res = self.client.get(get_detail_album_url(album2.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.put(
            get_detail_album_url(album2.id), {'title': 'test1'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.client.patch(
            get_detail_album_url(album2.id), {'title': 'test1'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.client.put(
            get_detail_album_url(album2.id), {'title': 'test1'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.client.delete(get_detail_album_url(album2.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_album_allowed_methods(self):
        self.client.force_authenticate(user=self.user)
        album = sample_album(owner=self.user, title='testalbum1')

        res = self.client.get(get_detail_album_url(album.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.patch(
            get_detail_album_url(album.id), {'title': 'test1'})
        album.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(album.title, 'test1')
        self.assertNotEqual('testalbum1', res.data['title'])

        res = self.client.put(
            get_detail_album_url(album.id), {'title': 'test2'})
        album.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(album.title, 'test2')
        self.assertNotEqual('test1', res.data['title'])

        res = self.client.delete(get_detail_album_url(album.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_pagination(self):
        for _ in range(59):
            sample_album(owner=self.user, title=f'testalbum{_}')
        # Check first page
        res = self.client.get(ALBUM_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('results', res.data)
        self.assertIn('count', res.data)
        self.assertTrue(res.data['next'])
        self.assertFalse(res.data['previous'])
        # Check next page
        res = self.client.get(res.data['next'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('results', res.data)
        self.assertIn('count', res.data)
        self.assertTrue(res.data['next'])
        self.assertTrue(res.data['previous'])
        # Check last page
        res = self.client.get(res.data['next'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('results', res.data)
        self.assertIn('count', res.data)
        self.assertFalse(res.data['next'])
        self.assertTrue(res.data['previous'])

    def test_like_an_album_unauthenticated(self):
        res = self.client.post(like_album_url(self.album.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_like_an_album(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.album.likes.count(), 0)
        # Create like.
        res = self.client.post(like_album_url(self.album.pk))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.album.refresh_from_db()
        self.assertEqual(self.album.likes.count(), 1)
        # Try create like while already liked.
        res = self.client.post(like_album_url(self.album.pk))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.album.refresh_from_db()
        self.assertEqual(self.album.likes.count(), 1)

    def test_like_other_users_albums(self):
        self.client.force_authenticate(self.user)
        album2 = sample_album(
            title='test2', owner=sample_user(
                email='test2@email.com', name='testname2',
                password='Testpassword123!'))
        self.assertEqual(album2.likes.count(), 0)
        # Create like.
        res = self.client.post(like_album_url(album2.pk))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        album2.refresh_from_db()
        self.assertEqual(album2.likes.count(), 1)
        # Try create like already liked.
        res = self.client.post(like_album_url(album2.pk))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        album2.refresh_from_db()
        self.assertEqual(album2.likes.count(), 1)

    def test_dislike_an_album_unauthenticated(self):
        res = self.client.delete(like_album_url(self.album.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dislike_an_album(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.album.likes.count(), 0)
        # Create like.
        res = self.client.post(like_album_url(self.album.pk))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.album.refresh_from_db()
        self.assertEqual(self.album.likes.count(), 1)
        # Dislike.
        res = self.client.delete(like_album_url(self.album.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.album.refresh_from_db()
        self.assertEqual(self.album.likes.count(), 0)
        # Try dislike already disliked.
        res = self.client.delete(like_album_url(self.album.pk))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

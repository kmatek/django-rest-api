from rest_framework import viewsets, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import action

from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from .permissions import IsOwnerOrReadOnly
from .serializers import (
    AlbumSerializer,
    AlbumDetailSerializer,
    AlbumPhotoSerializer
)

from core.models import Album, AlbumLike, AlbumPhoto


class CustomPaginator(PageNumberPagination):
    """Override page_size."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000


class AlbumAPIViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all().order_by('-id')
    serializer_class = AlbumSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrReadOnly
    )
    pagination_class = CustomPaginator

    def perform_create(self, serializer):
        """Create an album with authenticated user."""
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        """Change serializer class according to action."""
        if self.action in ('retrieve', 'update', 'partial_update'):
            self.serializer_class = AlbumDetailSerializer
        if self.action == 'upload_photo':
            self.serializer_class = AlbumPhotoSerializer
        return self.serializer_class

    @action(detail=True, methods=['post', 'delete'],
            url_path='like', name='like-album')
    def like_album(self, request, pk=None):
        """Like/dislike an album action."""
        try:
            like = AlbumLike.objects.get(
                album=self.get_object(), user_liked=request.user)
            # Dislike an album.
            if request.method == 'DELETE':
                like.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        except AlbumLike.DoesNotExist:
            # Like an album
            if request.method == 'POST':
                AlbumLike.objects.create(
                    album=self.get_object(), user_liked=request.user)
                return Response(status=status.HTTP_201_CREATED)
        # Liked/disliked handling.
        msg = _('Already liked or disliked.')
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'],
            url_path='upload-photo', name='upload-photo')
    def upload_photo(self, request, pk=None):
        """Upload photo to an album action."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], name='delete-photo',
            url_path='delete-photo/(?P<photo_pk>\w+)',) # noqa
    def delete_photo(self, request, pk=None, photo_pk=None):
        """Delete photo from an album action."""
        image = get_object_or_404(AlbumPhoto, pk=photo_pk)
        if image.album == self.get_object():
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        msg = _('Wrong album.')
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

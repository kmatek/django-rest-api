from rest_framework import viewsets, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import action

from django.utils.translation import gettext_lazy as _

from .permissions import IsOwnerOrReadOnly
from .serializers import AlbumSerializer, AlbumDetailSerializer

from core.models import Album, AlbumLike


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

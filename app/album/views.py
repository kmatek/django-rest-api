from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination

from .permissions import IsOwnerOrReadOnly
from .serializers import AlbumSerializer, AlbumDetailSerializer

from core.models import Album


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

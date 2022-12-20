from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import AlbumAPIViewSet

router = DefaultRouter()
router.register('', AlbumAPIViewSet)

app_name = 'album'

urlpatterns = [
    path('', include(router.urls)),
]

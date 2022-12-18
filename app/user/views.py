from rest_framework import generics, permissions

from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserImageSerializer,
    UserPasswordChangeSerializer,
)


class CreateUserAPIView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)


class UserDetailAPIView(generics.RetrieveAPIView):
    serializer_class = UserDetailSerializer

    def get_object(self):
        """Return authenticated user."""
        return self.request.user


class UserImageUploadAPIView(generics.UpdateAPIView):
    serializer_class = UserImageSerializer

    def get_object(self):
        """Return authenticated user."""
        return self.request.user


class UserPasswordChangeAPIView(generics.UpdateAPIView):
    serializer_class = UserPasswordChangeSerializer

    def get_object(self):
        """Return authenticated user."""
        return self.request.user

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.exceptions import Throttled

from django.utils.translation import gettext_lazy as _

from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserImageSerializer,
    UserPasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
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


class PasswordResetRequestAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = []

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            # Append throttling after successful attempt.
            if not self.throttle_classes:
                self.throttle_classes.append(AnonRateThrottle)
            msg = _('We have sent you an email.')
            return Response({'detail': msg}, status=status.HTTP_200_OK)

    def throttled(self, request, wait):
        msg = _("You can reset your password only once a day.")
        raise Throttled(detail={'detail': msg})


class PasswordResetConfirmAPIView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            msg = _('Password changed successfuly.')
            return Response({'detail': msg}, status=status.HTTP_200_OK)

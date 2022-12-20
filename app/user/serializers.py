from PIL import Image
from io import BytesIO

from rest_framework import serializers

from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator as token_generator # noqa

from .validators import SymbolValidator

from core.utils import (
    image_size_validator,
    image_dimensions_validator,
    is_image_gif_ext,
    EmailSender
)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ['email', 'name', 'password', 'is_active']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 8,
                'style': {'input_type': 'password'}
            },
            'name': {'min_length': 5},
            'is_active': {'read_only': True},
        }

    def validate_name(self, value):
        """Check if the name has any symbols."""
        try:
            SymbolValidator().validate_name(name=value)
            return value
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

    def validate_password(self, value):
        """Run password validations."""
        try:
            password_validation.validate_password(password=value)
            return value
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)


class UserDetailSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        """Added image field."""
        fields = UserSerializer.Meta.fields + ['image']


class UserImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(
        validators=(
            image_size_validator,
            is_image_gif_ext,
            image_dimensions_validator
        ),
        required=True)

    class Meta:
        model = get_user_model()
        fields = ('image',)

    def validate_image(self, value):
        """Image resizing."""
        io_img = BytesIO()
        with Image.open(value) as image:
            image.thumbnail((200, 200))
            image.save(io_img, 'png', quality=100, subsampling=0)
            return InMemoryUploadedFile(
                io_img, 'image', 'image.png',
                'PNG', io_img.tell(), None)


class UserPasswordChangeSerializer(UserDetailSerializer):
    new_password = serializers.CharField(
        write_only=True, min_length=8,
        required=True, style={'input_type': 'password'})

    class Meta(UserDetailSerializer.Meta):
        """Set up read_only_fields."""
        fields = UserDetailSerializer.Meta.fields + ['new_password']
        read_only_fields = ('email', 'name', 'is_active', 'image')

    def validate_password(self, value):
        """Check that the old_password is correct."""
        user = self.context.get('view').get_object()
        if not user.check_password(value):
            msg = _('Old password is incorrect.')
            raise serializers.ValidationError(msg)

    def validate_new_password(self, value):
        # Check that the new_password is not similar to the old one.
        user = self.context.get('view').get_object()
        if user.check_password(value):
            msg = _('The new password is similar to the old one.')
            raise serializers.ValidationError(msg)
        # Run validation for the new passowrd
        try:
            password_validation.validate_password(password=value)
            return value
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

    def update(self, instance, validated_data):
        """Update user password."""
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)

    def validate_email(self, value):
        """Check that user exists."""
        try:
            user = get_user_model().objects.get(email=value)
            return user
        except get_user_model().DoesNotExist:
            msg = _('No user exists with this email.')
            raise serializers.ValidationError(msg)

    def save(self):
        """Send an email."""
        user = self.validated_data['email']
        sender = EmailSender(user)
        message = sender.make_message()
        sender.send_email('Reset password', message)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, write_only=True)
    user_id = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        min_length=8, required=True,
        write_only=True, style={'input_type': 'password'})

    def validate_user_id(self, value):
        """Check that user exists."""
        try:
            decoded_user_id = urlsafe_base64_decode(value).decode()
            user = get_user_model().objects.get(pk=decoded_user_id)
            return user
        except get_user_model().DoesNotExist:
            msg = _('User does not exist.')
            raise serializers.ValidationError(msg)
        except UnicodeDecodeError:
            msg = _('Wrong user_id.')
            raise serializers.ValidationError(msg)

    def validate_new_password(self, value):
        try:
            password_validation.validate_password(password=value)
            return value
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

    def validate(self, data):
        user = data.get('user_id')
        token = data.get('token')
        # Check that the token is active.
        if not token_generator.check_token(user, token):
            msg = _('Token has expired.')
            raise serializers.ValidationError({'token': msg})
        # Check that the new password is not simmilar to the old one.
        new_password = data.get('new_password')
        if user.check_password(new_password):
            msg = _('The new password is similar to the old one.')
            raise serializers.ValidationError({'new_password': msg})

        return data

    def save(self):
        """Changing the user's password."""
        user = self.validated_data['user_id']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()


class ActivateUserSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, write_only=True)
    user_id = serializers.CharField(required=True, write_only=True)

    def validate_user_id(self, value):
        """Check that user exists."""
        try:
            decoded_user_id = urlsafe_base64_decode(value).decode()
            user = get_user_model().objects.get(pk=decoded_user_id)
            if user.is_active:
                msg = _('User is already active.')
                raise serializers.ValidationError(msg)
            return user
        except get_user_model().DoesNotExist:
            msg = _('User does not exist.')
            raise serializers.ValidationError(msg)
        except UnicodeDecodeError:
            msg = _('Wrong user_id.')
            raise serializers.ValidationError(msg)

    def validate_token(self, value):
        """Check that user is already active."""
        try:
            decoded_uuid = urlsafe_base64_decode(value).decode()
            user = get_user_model().objects.get(activation_uuid=decoded_uuid)
            if user.activation_uuid.hex == decoded_uuid:
                msg = _('Invalid activation token.')
                raise serializers.ValidationError(msg)
            return decoded_uuid
        except get_user_model().DoesNotExist:
            msg = _('User does not exist.')
            raise serializers.ValidationError(msg)
        except UnicodeDecodeError:
            msg = _('Wrong token.')
            raise serializers.ValidationError(msg)

    def save(self):
        """Activate new user."""
        user = self.validated_data['user_id']
        user.is_active = True
        user.save()

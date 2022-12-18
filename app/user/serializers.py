from PIL import Image
from io import BytesIO

from rest_framework import serializers

from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from .validators import SymbolValidator

from core.utils import (
    image_size_validator,
    image_dimensions_validator,
    is_image_gif_ext,
)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ['email', 'name', 'password', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'name': {'min_length': 5},
            'is_active': {'read_only': True}
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
        write_only=True, min_length=8, required=True)

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

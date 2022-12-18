import os
import uuid

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)

from .utils import (
    image_size_validator,
    is_image_gif_ext,
    image_dimensions_validator
)


def user_image_file_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'profile_pics', instance.email, filename)


class UserManager(BaseUserManager):
    """Modify creating a new user/superuser."""
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        if not name:
            raise ValueError('User must have a name')

        user = self.model(
            email=self.normalize_email(email),
            name=name.lower(),
            **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, name, password):
        super_user = self.create_user(email, name, password)
        super_user.is_staff = True
        super_user.is_active = True
        super_user.is_superuser = True
        super_user.save(using=self._db)

        return super_user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True, blank=False)
    name = models.CharField(max_length=30, unique=True, blank=False)
    image = models.ImageField(null=True, blank=True,
                              upload_to=user_image_file_path,
                              validators=[
                                is_image_gif_ext,
                                image_size_validator,
                                image_dimensions_validator])
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    activation_uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

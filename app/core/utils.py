from django.core.files.images import get_image_dimensions
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.utils.encoding import smart_bytes
from django.utils.http import urlsafe_base64_encode

from .tasks import send_email


def image_size_validator(image):
    """Validate that an image size is not bigger than 1MB."""
    if image.size > 1024 * 1024:
        msg = _('Max image file is 1MB')
        raise ValidationError(msg)


def image_dimensions_validator(image):
    """Validate that an image dimensions are not less than 200x200."""
    width, height = get_image_dimensions(image)

    if width < 200 or height < 200:
        msg = _('The dimensions of the image must not be less than 200x200.')
        raise ValidationError(msg)


def is_image_gif_ext(image):
    """Validate that an image extension is not a gif."""
    if image.name.endswith('.gif') or image.name.endswith('.GIF'):
        msg = _('Gif extensions are not allowed.')
        raise ValidationError(msg)


class EmailSender:
    """An email sending handler for activation and password reset."""

    def __init__(self, user: get_user_model):
        self.user = user
        self.domain = Site.objects.get_current()

    def make_url(self, activation: bool = False) -> str:
        """Create activation/reset-password link."""
        encoded_user_id = urlsafe_base64_encode(smart_bytes(self.user.pk)) # noqa

        if activation:
            # Create activation link.
            activation_uuid = self.user.activation.hex
            encoded_activation_uuid = urlsafe_base64_encode( # noqa
                smart_bytes(activation_uuid))
            url = 'some url'
        else:
            token = default_token_generator.make_token(self.user) # noqa
            url = 'some url'

        return url

    def send_email(self, title: str, message: str):
        return send_email.delay(title, message, self.user.email)

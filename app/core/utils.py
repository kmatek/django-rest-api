from django.core.files.images import get_image_dimensions
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


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

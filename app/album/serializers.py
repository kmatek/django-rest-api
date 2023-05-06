from rest_framework import serializers

from django.utils.translation import gettext_lazy as _
from django.conf import settings

from core.models import Album, AlbumPhoto
from core.utils import is_image_gif_ext, image_size_validator


class AlbumSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField()
    likes = serializers.IntegerField(source='likes.count', read_only=True)

    class Meta:
        model = Album
        fields = '__all__'
        read_only_fields = ('owner', 'id')

    def validate(self, data):
        """Check that user has no more than 3 albums."""
        user = self.context.get('request').user
        number_of_albums = user.album_set.count()
        if number_of_albums == settings.ALBUM_LIMIT:
            msg = _(f'There are only available {settings.ALBUM_LIMIT} albums.')
            raise serializers.ValidationError({'album': msg})
        return data


class AlbumPhotoSerializer(serializers.HyperlinkedModelSerializer):
    image = serializers.ImageField(
        allow_empty_file=False, validators=(
            is_image_gif_ext,
            image_size_validator
        ))

    class Meta:
        model = AlbumPhoto
        fields = ('id', 'image')

    def validate(self, data):
        """Check that album does not have no more that 10 photos."""
        album = self.context.get('view').get_object()
        number_of_photos = settings.ALBUM_PHOTOS_LIMIT - album.images.count()
        if not number_of_photos:
            msg = _(f"Ensure that an album has no more than {settings.ALBUM_PHOTOS_LIMIT} elements.") # noqa
            raise serializers.ValidationError({'image': msg})
        return {'album': album, 'image': data.get('image')}


class AlbumDetailSerializer(AlbumSerializer):
    images = AlbumPhotoSerializer(many=True, read_only=True)

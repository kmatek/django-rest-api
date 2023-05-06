from django.contrib import admin
from django.utils.translation import gettext as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Album, AlbumLike, AlbumPhoto


class UserAdmin(BaseUserAdmin):
    ordering = ('id',)
    list_display = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name', 'image')}),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser')}
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2')
        }),
    )
    search_fields = ('email',)
    search_help_text = 'Search by email'


admin.site.register(User, UserAdmin)
admin.site.register(Album)
admin.site.register(AlbumLike)
admin.site.register(AlbumPhoto)

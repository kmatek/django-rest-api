from django.urls import path

from . import views as api_views

app_name = 'user'

urlpatterns = [
    path('create/',
         api_views.CreateUserAPIView.as_view(),
         name='create-user'),
    path('me/', api_views.UserDetailAPIView.as_view(), name='detail-user'),
    path('me/upload-image/',
         api_views.UserImageUploadAPIView.as_view(),
         name='upload-image-user'),
    path('change-password/',
         api_views.UserPasswordChangeAPIView.as_view(),
         name='change-user-password'),
    path('reset-password/',
         api_views.PasswordResetRequestAPIView.as_view(),
         name='reset-password'),
    path('reset-password-confirm/',
         api_views.PasswordResetConfirmAPIView.as_view(),
         name='reset-password-confirm'),
    path('activate/<uidb64>/<token>/',
         api_views.ActivateUserAPIView.as_view(),
         name='activate-user')
]

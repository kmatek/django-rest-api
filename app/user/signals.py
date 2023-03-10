import functools
import os
import shutil

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings

from core.utils import EmailSender


def suspendingreceiver(signal, **decorator_kwargs):
    def our_wrapper(func):
        @receiver(signal, **decorator_kwargs)
        @functools.wraps(func)
        def fake_receiver(sender, **kwargs):
            if settings.SUSPEND_SIGNALS:
                return
            return func(sender, **kwargs)
        return fake_receiver
    return our_wrapper


@suspendingreceiver(post_save, sender=get_user_model())
def send_activation_email(sender, instance, created, **kwargs):
    if created:
        sender = EmailSender(instance)
        message = sender.make_message(activation=True)
        sender.send_email('Activate account', message)


@receiver(post_delete, sender=get_user_model())
def delete_user_folder(sender, instance, using, **kwargs):
    # Remove albums.
    path = f'/vol/web/media/uploads/albums/{instance.email}'
    if os.path.exists(path):
        shutil.rmtree(path)
    # Remove profile_pic
    path = f'/vol/web/media/uploads/profile_pics/{instance.email}'
    if os.path.exists(path):
        shutil.rmtree(path)

# accounts/signals.py

"""
Сигналы для автоматического создания профиля и других действий.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматическое создание профиля при создании пользователя"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохранение профиля при сохранении пользователя"""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Действия при входе пользователя"""
    # Обновление времени последнего входа
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])

    # Запись в лог
    print(f"User {user.username} logged in at {timezone.now()}")


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """Действия при выходе пользователя"""
    if user:
        print(f"User {user.username} logged out at {timezone.now()}")


@receiver(pre_save, sender=User)
def user_pre_save_handler(sender, instance, **kwargs):
    """Действия перед сохранением пользователя"""
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            # Проверка изменений email
            if old_instance.email != instance.email:
                instance.email_verified = False
        except User.DoesNotExist:
            pass

# notifications/models.py

"""
Модели для управления уведомлениями.
"""

from django.db import models
from django.urls import reverse
from core.models import TimeStampedModel
# notifications/models.py
import re
from django.contrib.auth import get_user_model

User = get_user_model()

def extract_mentions(text):
    """Возвращает список пользователей, упомянутых через @username в тексте"""
    pattern = r'@(\w+)'
    usernames = re.findall(pattern, text)
    return User.objects.filter(username__in=usernames)


class Notification(TimeStampedModel):
    """
    Модель уведомления.
    """

    class NotificationType(models.TextChoices):
        INFO = 'info', 'Информация'
        SUCCESS = 'success', 'Успех'
        WARNING = 'warning', 'Предупреждение'
        ERROR = 'error', 'Ошибка'

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь'
    )

    type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        verbose_name='Тип уведомления'
    )

    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок'
    )

    message = models.TextField(
        verbose_name='Сообщение'
    )

    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Прочитано'
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата прочтения'
    )

    link = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Ссылка'
    )

    # после поля link
    email_sent = models.BooleanField(default=False, verbose_name='Email отправлен')

    def send_email(self):
        """Отправка email‑уведомления (если пользователь подписан)"""
        if self.user.notification_settings.get('email_enabled', False) and not self.email_sent:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                subject=self.title,
                message=self.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                fail_silently=True,
            )
            self.email_sent = True
            self.save(update_fields=['email_sent'])

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"

    def mark_as_read(self):
        """Отметить как прочитанное"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class NotificationPreference(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='notification_prefs')
    email_enabled = models.BooleanField(default=True, verbose_name='Получать email‑уведомления')
    # Категории событий
    notify_client_created = models.BooleanField(default=True)
    notify_contract_created = models.BooleanField(default=True)
    notify_task_assigned = models.BooleanField(default=True)
    notify_task_overdue = models.BooleanField(default=True)
    # ... можно добавить другие

    class Meta:
        verbose_name = 'Настройки уведомлений'
        verbose_name_plural = 'Настройки уведомлений'

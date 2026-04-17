# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    """
    Расширенная модель пользователя.
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Администратор'
        MANAGER = 'MANAGER', 'Менеджер'
        SALES = 'SALES', 'Продажник'
        SUPPORT = 'SUPPORT', 'Поддержка'
        VIEWER = 'VIEWER', 'Наблюдатель'

    # Основные поля
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        verbose_name='Роль'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )

    # Профессиональная информация
    position = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Должность'
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Отдел'
    )

    hire_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата найма'
    )

    employee_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        verbose_name='Табельный номер'
    )

    # Настройки
    email_notifications = models.BooleanField(
        default=True,
        verbose_name='Email уведомления'
    )

    # Настройки интерфейса
    theme = models.CharField(
        max_length=20,
        default='light',
        choices=[('light', 'Светлая'), ('dark', 'Тёмная')],
        verbose_name='Тема оформления'
    )

    language = models.CharField(
        max_length=10,
        default='ru',
        choices=[('ru', 'Русский'), ('en', 'English')],
        verbose_name='Язык'
    )

    timezone = models.CharField(
        max_length=50,
        default='Europe/Moscow',
        verbose_name='Часовой пояс'
    )

    telegram_notifications = models.BooleanField(
        default=False,
        verbose_name='Уведомления в Telegram'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name or self.username} ({self.get_role_display()})"

    def get_full_name(self):
        full_name = super().get_full_name()
        return full_name or self.username

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    # ДОБАВЛЯЕМ ЭТО СВОЙСТВО
    @property
    def profile(self):
        """
        Получение профиля пользователя.
        Если профиль не существует, создаётся автоматически.
        """
        try:
            return UserProfile.objects.get(user=self)
        except UserProfile.DoesNotExist:
            return UserProfile.objects.create(user=self)


class UserProfile(models.Model):
    """
    Расширенный профиль пользователя (дополнительная информация).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    company = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Компания')

    # Личная информация
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )

    # Контактная информация для экстренных случаев
    emergency_contact = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Контакт для экстренных случаев'
    )

    emergency_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон для экстренных случаев'
    )

    # Социальные сети
    telegram = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Telegram'
    )

    linkedin = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='LinkedIn'
    )

    # Настройки
    notification_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Настройки уведомлений'
    )

    interface_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Настройки интерфейса'
    )

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f"Профиль {self.user.get_full_name() or self.user.username}"
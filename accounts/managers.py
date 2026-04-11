# accounts/managers.py

"""
Менеджеры для моделей пользователей.
"""

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """
    Менеджер для модели User с методами создания пользователей.
    """

    def create_user(self, username, email=None, password=None, **extra_fields):
        """Создание обычного пользователя"""
        if not username:
            raise ValueError('Username must be set')

        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

    def get_admins(self):
        """Получение всех администраторов"""
        return self.filter(role__in=['ADMIN', 'DIRECTOR'], is_active=True)

    def get_managers(self):
        """Получение всех менеджеров"""
        return self.filter(role__in=['ADMIN', 'DIRECTOR', 'MANAGER'], is_active=True)

    def get_active_employees(self):
        """Получение активных сотрудников"""
        return self.filter(is_active=True, fire_date__isnull=True)

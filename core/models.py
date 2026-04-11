# core/models.py

"""
Базовые абстрактные модели для всех приложений CRM.
Содержит общие поля и функциональность, используемые во всем проекте.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


class TimeStampedModel(models.Model):
    """
    Абстрактная модель, добавляющая поля даты создания и обновления.
    
    Поля:
        created_at: Дата и время создания записи
        updated_at: Дата и время последнего обновления записи
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def get_created_at_display(self):
        """Возвращает отформатированную дату создания"""
        return self.created_at.strftime('%d.%m.%Y %H:%M')

    def get_updated_at_display(self):
        """Возвращает отформатированную дату обновления"""
        return self.updated_at.strftime('%d.%m.%Y %H:%M')


class StatusModel(models.Model):
    """
    Абстрактная модель с полем статуса и отслеживанием изменений.
    
    Поля:
        status: Текущий статус записи
        status_changed_at: Дата последнего изменения статуса
        status_changed_by: Пользователь, изменивший статус
        status_comment: Комментарий к изменению статуса
    """
    
    class StatusChoices(models.TextChoices):
        """Доступные статусы для записей"""
        ACTIVE = 'active', 'Активный'
        INACTIVE = 'inactive', 'Неактивный'
        PENDING = 'pending', 'В ожидании'
        ARCHIVED = 'archived', 'В архиве'
        DELETED = 'deleted', 'Удален'

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        db_index=True,
        verbose_name='Статус'
    )
    
    status_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата изменения статуса'
    )
    
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_status_changes',
        verbose_name='Изменил статус'
    )
    
    status_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий к изменению статуса'
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Переопределенный метод save для автоматического обновления
        даты изменения статуса при его изменении.
        """
        if self.pk:  # Если запись уже существует
            try:
                old_instance = self.__class__.objects.get(pk=self.pk)
                if old_instance.status != self.status:
                    self.status_changed_at = timezone.now()
            except self.__class__.DoesNotExist:
                pass
        else:  # Новая запись
            self.status_changed_at = timezone.now()
        
        super().save(*args, **kwargs)

    def activate(self, user=None, comment=''):
        """Активировать запись"""
        self.status = self.StatusChoices.ACTIVE
        self.status_changed_by = user
        self.status_comment = comment
        self.save()

    def deactivate(self, user=None, comment=''):
        """Деактивировать запись"""
        self.status = self.StatusChoices.INACTIVE
        self.status_changed_by = user
        self.status_comment = comment
        self.save()

    def archive(self, user=None, comment=''):
        """Архивировать запись"""
        self.status = self.StatusChoices.ARCHIVED
        self.status_changed_by = user
        self.status_comment = comment
        self.save()

    @property
    def is_active(self):
        """Проверка, активна ли запись"""
        return self.status == self.StatusChoices.ACTIVE

    @property
    def is_inactive(self):
        """Проверка, неактивна ли запись"""
        return self.status == self.StatusChoices.INACTIVE

    @property
    def is_pending(self):
        """Проверка, в ожидании ли запись"""
        return self.status == self.StatusChoices.PENDING

    @property
    def is_archived(self):
        """Проверка, в архиве ли запись"""
        return self.status == self.StatusChoices.ARCHIVED


class ContactInfoModel(models.Model):
    """
    Абстрактная модель с контактной информацией.
    
    Поля:
        email: Электронная почта
        phone: Основной телефон
        phone_secondary: Дополнительный телефон
        website: Веб-сайт
        address: Адрес
        city: Город
        country: Страна
        postal_code: Почтовый индекс
    """
    email = models.EmailField(
        max_length=255,
        blank=True,
        db_index=True,
        verbose_name='Email'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    
    phone_secondary = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Дополнительный телефон'
    )
    
    website = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='Веб-сайт'
    )
    
    address = models.TextField(
        blank=True,
        verbose_name='Адрес'
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Город'
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Страна'
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Почтовый индекс'
    )

    class Meta:
        abstract = True

    @property
    def full_address(self):
        """Возвращает полный адрес одной строкой"""
        parts = []
        if self.country:
            parts.append(self.country)
        if self.city:
            parts.append(self.city)
        if self.address:
            parts.append(self.address)
        if self.postal_code:
            parts.append(f"индекс: {self.postal_code}")
        return ', '.join(parts) if parts else 'Адрес не указан'

    @property
    def contact_info(self):
        """Возвращает контактную информацию в виде словаря"""
        return {
            'email': self.email,
            'phone': self.phone,
            'phone_secondary': self.phone_secondary,
            'website': self.website,
            'address': self.full_address,
        }


class NotesModel(models.Model):
    """
    Абстрактная модель с полями для заметок.
    
    Поля:
        notes: Общие заметки (видимые всем)
        private_notes: Приватные заметки (только для автора и админов)
    """
    notes = models.TextField(
        blank=True,
        verbose_name='Заметки'
    )
    
    private_notes = models.TextField(
        blank=True,
        verbose_name='Приватные заметки'
    )

    class Meta:
        abstract = True

    def get_notes_preview(self, length=100):
        """Возвращает превью заметок"""
        if self.notes:
            return self.notes[:length] + '...' if len(self.notes) > length else self.notes
        return 'Нет заметок'

    def get_private_notes_preview(self, length=100):
        """Возвращает превью приватных заметок"""
        if self.private_notes:
            return self.private_notes[:length] + '...' if len(self.private_notes) > length else self.private_notes
        return 'Нет приватных заметок'


class CreatorModel(models.Model):
    """
    Абстрактная модель с полями создателя и редактора.
    
    Поля:
        created_by: Пользователь, создавший запись
        updated_by: Пользователь, последним обновивший запись
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='Создал'
    )
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='Обновил'
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Автоматически обновляет updated_by при сохранении"""
        if self.pk and hasattr(self, '_current_user'):
            self.updated_by = self._current_user
        super().save(*args, **kwargs)

    def set_creator(self, user):
        """Устанавливает создателя записи"""
        if not self.pk and user:
            self.created_by = user

    def set_updater(self, user):
        """Устанавливает редактора записи"""
        if user:
            self._current_user = user


class NameSlugModel(models.Model):
    """
    Абстрактная модель с полями имени и slug для URL.
    
    Поля:
        name: Название объекта
        slug: URL-идентификатор (генерируется из name)
    """
    name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='Название'
    )
    
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name='URL-идентификатор'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Автоматически генерирует slug из name, если не указан"""
        if not self.slug and self.name:
            from django.utils.text import slugify
            self.slug = slugify(self.name)[:255]
        super().save(*args, **kwargs)


class SoftDeleteModel(models.Model):
    """
    Абстрактная модель с мягким удалением (не удаляет из БД физически).
    
    Поля:
        is_deleted: Флаг удаления
        deleted_at: Дата удаления
        deleted_by: Пользователь, удаливший запись
    """
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Удалено'
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата удаления'
    )
    
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted',
        verbose_name='Удалил'
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        Мягкое удаление - запись помечается как удаленная,
        но остается в базе данных.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self, using=None, keep_parents=False):
        """
        Жесткое удаление - запись физически удаляется из БД.
        """
        super().delete(using, keep_parents)

    def restore(self):
        """
        Восстановление из мягкого удаления.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    @property
    def is_deleted_status(self):
        """Проверка, удалена ли запись"""
        return self.is_deleted


class BaseModel(TimeStampedModel, StatusModel, NotesModel, CreatorModel):
    """
    Базовая модель, объединяющая все основные абстрактные модели.
    Используется как основа для большинства моделей в проекте.
    """
    
    class Meta:
        abstract = True

    def __str__(self):
        """
        Должен быть переопределен в дочерних классах.
        """
        return f"{self.__class__.__name__} #{self.pk}"

    def clean(self):
        """
        Валидация модели. Может быть переопределена в дочерних классах.
        """
        pass

    def full_clean(self, *args, **kwargs):
        """
        Полная валидация модели с вызовом clean().
        """
        super().full_clean(*args, **kwargs)
        self.clean()

    def get_status_badge(self):
        """
        Возвращает HTML-код для отображения статуса в виде бейджа.
        """
        status_colors = {
            self.StatusChoices.ACTIVE: 'success',
            self.StatusChoices.INACTIVE: 'secondary',
            self.StatusChoices.PENDING: 'warning',
            self.StatusChoices.ARCHIVED: 'info',
            self.StatusChoices.DELETED: 'danger',
        }
        color = status_colors.get(self.status, 'light')
        return f'<span class="badge bg-{color}">{self.get_status_display()}</span>'


class BaseTreeModel(BaseModel):
    """
    Базовая модель для древовидных структур (категории, отделы и т.д.).
    
    Поля:
        parent: Родительский элемент
        level: Уровень вложенности
        lft, rght, tree_id: Поля для работы с MPTT
    """
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родитель'
    )
    
    level = models.IntegerField(
        default=0,
        editable=False,
        verbose_name='Уровень'
    )
    
    lft = models.IntegerField(
        default=0,
        editable=False,
        verbose_name='Левый ключ'
    )
    
    rght = models.IntegerField(
        default=0,
        editable=False,
        verbose_name='Правый ключ'
    )
    
    tree_id = models.IntegerField(
        default=0,
        editable=False,
        verbose_name='ID дерева'
    )

    class Meta:
        abstract = True

    def get_ancestors(self):
        """Возвращает всех предков"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Возвращает всех потомков"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    @property
    def indent_title(self):
        """Возвращает название с отступами для отображения дерева"""
        return '—' * self.level + ' ' + self.name if self.level > 0 else self.name
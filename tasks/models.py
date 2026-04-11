# tasks/models.py

"""
Модели для управления задачами.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from core.models import BaseModel


class Task(BaseModel):
    """
    Модель задачи.
    """

    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'В работе'
        COMPLETED = 'completed', 'Завершена'
        CANCELLED = 'cancelled', 'Отменена'

    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        MEDIUM = 'medium', 'Средний'
        HIGH = 'high', 'Высокий'
        URGENT = 'urgent', 'Срочный'

    # Связи
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True,
        verbose_name='Клиент'
    )

    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True,
        verbose_name='Контракт'
    )

    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='Исполнитель'
    )

    # Основная информация
    title = models.CharField(
        max_length=500,
        verbose_name='Название',
        db_index=True
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name='Приоритет',
        db_index=True
    )

    # Даты
    due_date = models.DateTimeField(
        verbose_name='Срок выполнения',
        db_index=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата выполнения'
    )

    # Дополнительные поля
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Оценка времени (часы)'
    )

    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Фактическое время (часы)'
    )

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['due_date', '-priority']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tasks:task_detail', args=[self.id])

    @property
    def is_overdue(self):
        """Проверка на просрочку"""
        from django.utils import timezone
        return (self.due_date < timezone.now() and
                self.status not in ['completed', 'archived'])

    @property
    def time_difference(self):
        """Разница между оценкой и фактическим временем"""
        if self.estimated_hours and self.actual_hours:
            return self.actual_hours - self.estimated_hours
        return None

    @property
    def priority_color(self):
        """Цвет приоритета для отображения"""
        colors = {
            'low': 'success',
            'medium': 'info',
            'high': 'warning',
            'urgent': 'danger'
        }
        return colors.get(self.priority, 'secondary')


class TaskComment(BaseModel):
    """
    Комментарии к задачам.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Задача'
    )

    comment = models.TextField(
        verbose_name='Комментарий'
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']

    def __str__(self):
        return f"Комментарий к {self.task} от {self.created_at}"

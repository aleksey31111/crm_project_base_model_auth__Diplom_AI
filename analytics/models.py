# analytics/models.py

"""
Модели для аналитики и отчетов.
"""

from django.db import models
from core.models import TimeStampedModel


class Report(TimeStampedModel):
    """
    Модель отчета.
    """

    class ReportType(models.TextChoices):
        SALES = 'sales', 'Продажи'
        CLIENTS = 'clients', 'Клиенты'
        TASKS = 'tasks', 'Задачи'
        CONTRACTS = 'contracts', 'Контракты'

    class ReportFormat(models.TextChoices):
        PDF = 'pdf', 'PDF'
        EXCEL = 'excel', 'Excel'
        CSV = 'csv', 'CSV'

    name = models.CharField(
        max_length=255,
        verbose_name='Название отчета'
    )

    type = models.CharField(
        max_length=20,
        choices=ReportType.choices,
        verbose_name='Тип отчета'
    )

    format = models.CharField(
        max_length=20,
        choices=ReportFormat.choices,
        default=ReportFormat.EXCEL,
        verbose_name='Формат'
    )

    parameters = models.JSONField(
        default=dict,
        verbose_name='Параметры'
    )

    file = models.FileField(
        upload_to='reports/',
        null=True,
        blank=True,
        verbose_name='Файл отчета'
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reports',
        verbose_name='Создал'
    )

    class Meta:
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчеты'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.created_at})"

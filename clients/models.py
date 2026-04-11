# clients/models.py

"""
Модели для управления клиентами.
"""

from django.db import models
from django.core.validators import MinLengthValidator
from django.urls import reverse
from core.models import BaseModel, ContactInfoModel


class Client(BaseModel, ContactInfoModel):
    """
    Модель клиента.
    """

    class ClientType(models.TextChoices):
        INDIVIDUAL = 'individual', 'Физическое лицо'
        COMPANY = 'company', 'Юридическое лицо'
        ENTREPRENEUR = 'entrepreneur', 'Индивидуальный предприниматель'

    # Основная информация
    type = models.CharField(
        max_length=20,
        choices=ClientType.choices,
        default=ClientType.INDIVIDUAL,
        verbose_name='Тип клиента',
        db_index=True
    )

    full_name = models.CharField(
        max_length=500,
        verbose_name='Полное наименование',
        db_index=True
    )

    short_name = models.CharField(
        max_length=255,
        verbose_name='Краткое наименование',
        blank=True
    )

    # Для юридических лиц
    inn = models.CharField(
        max_length=12,
        blank=True,
        validators=[MinLengthValidator(10)],
        verbose_name='ИНН',
        db_index=True
    )

    kpp = models.CharField(
        max_length=9,
        blank=True,
        verbose_name='КПП'
    )

    ogrn = models.CharField(
        max_length=15,
        blank=True,
        verbose_name='ОГРН'
    )

    # Для физических лиц
    first_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Имя'
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Фамилия'
    )

    patronymic = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Отчество'
    )

    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )

    # Дополнительные поля
    manager = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_clients',
        verbose_name='Ответственный менеджер'
    )

    source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Источник'
    )

    company = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Компания'
    )

    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Должность'
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type', 'status']),
            models.Index(fields=['full_name']),
            models.Index(fields=['inn']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.full_name or self.short_name or f"Клиент #{self.id}"

    def get_absolute_url(self):
        return reverse('clients:client_detail', args=[self.id])

    def save(self, *args, **kwargs):
        """Автоматическое заполнение short_name если не указано"""
        if not self.short_name and self.full_name:
            self.short_name = self.full_name[:255]
        super().save(*args, **kwargs)

    @property
    def full_address(self):
        """Полный адрес одной строкой"""
        parts = []
        if self.country:
            parts.append(self.country)
        if self.city:
            parts.append(self.city)
        if self.address:
            parts.append(self.address)
        if self.postal_code:
            parts.append(self.postal_code)
        return ', '.join(parts)

    @property
    def contract_count(self):
        """Количество контрактов клиента"""
        return self.contracts.count()

    @property
    def total_contract_amount(self):
        """Общая сумма контрактов"""
        from django.db.models import Sum
        return self.contracts.aggregate(Sum('amount'))['amount__sum'] or 0

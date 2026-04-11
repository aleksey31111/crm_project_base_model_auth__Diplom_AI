# contracts/models.py

"""
Модели для управления контрактами.
"""

from datetime import date
from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from core.models import BaseModel


class Contract(BaseModel):
    """
    Модель контракта.
    """

    class ContractType(models.TextChoices):
        SALE = 'sale', 'Продажа'
        SERVICE = 'service', 'Услуга'
        MAINTENANCE = 'maintenance', 'Обслуживание'
        LEASE = 'lease', 'Аренда'
        CONSULTING = 'consulting', 'Консалтинг'

    class PaymentStatus(models.TextChoices):
        NOT_PAID = 'not_paid', 'Не оплачен'
        PARTIALLY_PAID = 'partially_paid', 'Частично оплачен'
        PAID = 'paid', 'Оплачен'
        OVERDUE = 'overdue', 'Просрочен'

    # Связи
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name='Клиент'
    )

    # Основная информация
    number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Номер договора',
        db_index=True
    )

    type = models.CharField(
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.SERVICE,
        verbose_name='Тип договора'
    )

    title = models.CharField(
        max_length=500,
        verbose_name='Название'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )

    # Даты
    start_date = models.DateField(
        verbose_name='Дата начала'
    )

    end_date = models.DateField(
        verbose_name='Дата окончания'
    )

    signed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата подписания'
    )

    # Финансовая информация
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Сумма'
    )

    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Оплачено'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.NOT_PAID,
        verbose_name='Статус оплаты',
        db_index=True
    )

    # Управление
    manager = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_contracts',
        verbose_name='Ответственный менеджер'
    )

    # Файлы
    document = models.FileField(
        upload_to='contracts/documents/',
        blank=True,
        null=True,
        verbose_name='Файл договора'
    )

    class Meta:
        verbose_name = 'Контракт'
        verbose_name_plural = 'Контракты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        permissions = [
            ('can_view_all_contracts', 'Может просматривать все контракты'),
            ('can_edit_all_contracts', 'Может редактировать все контракты'),
            ('can_delete_all_contracts', 'Может удалять все контракты'),
            ('can_manage_payments', 'Может управлять оплатами'),
        ]
    def __str__(self):
        return f"{self.number} - {self.title}"

    def get_absolute_url(self):
        return reverse('contracts:contract_detail', args=[self.id])

    def save(self, *args, **kwargs):
        """Автоматический расчет статуса оплаты"""
        if self.paid_amount >= self.amount:
            self.payment_status = self.PaymentStatus.PAID
        elif self.paid_amount > 0:
            self.payment_status = self.PaymentStatus.PARTIALLY_PAID
        else:
            self.payment_status = self.PaymentStatus.NOT_PAID
        super().save(*args, **kwargs)

    @property
    def remaining_amount(self):
        """Оставшаяся сумма к оплате"""
        return self.amount - self.paid_amount

    @property
    def is_overdue(self):
        """Проверка на просрочку"""
        from django.utils import timezone
        return self.end_date < timezone.now().date() and self.payment_status != self.PaymentStatus.PAID

    @property
    def payment_percentage(self):
        """Процент оплаты"""
        if self.amount > 0:
            return (self.paid_amount / self.amount) * 100
        return 0


class Payment(models.Model):
    """
    Модель оплаты по контракту.
    """
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Наличные'
        BANK_TRANSFER = 'bank_transfer', 'Банковский перевод'
        CARD = 'card', 'Банковская карта'
        ELECTRONIC = 'electronic', 'Электронные деньги'

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Контракт'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Сумма платежа'
    )
    payment_date = models.DateField(
        default=date.today,
        verbose_name='Дата оплаты'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.BANK_TRANSFER,
        verbose_name='Способ оплаты'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments_created',
        verbose_name='Кем добавлен'
    )

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплаты'
        ordering = ['-payment_date']

    def __str__(self):
        return f"Оплата по {self.contract.number}: {self.amount} руб."
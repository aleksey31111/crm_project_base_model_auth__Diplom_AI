# contracts/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from .models import Payment, Contract


def update_contract_payment_status(contract):
    """
    Обновляет оплаченную сумму контракта на основе успешных платежей.
    """
    total_paid = contract.payments.filter(yookassa_status='succeeded').aggregate(total=Sum('amount'))['total'] or 0
    if contract.paid_amount != total_paid:
        contract.paid_amount = total_paid
        contract.save()  # save() вызовет пересчёт payment_status в модели Contract


@receiver(post_save, sender=Payment)
def payment_saved(sender, instance, **kwargs):
    """При сохранении платежа обновляем контракт, если платёж успешен."""
    if instance.yookassa_status == 'succeeded':
        update_contract_payment_status(instance.contract)


@receiver(post_delete, sender=Payment)
def payment_deleted(sender, instance, **kwargs):
    """При удалении платежа пересчитываем сумму оплаты по контракту."""
    update_contract_payment_status(instance.contract)
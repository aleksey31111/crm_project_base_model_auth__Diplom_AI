# contracts/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from .models import Payment, Contract

def update_contract_payment_status(contract):
    """Обновляет оплаченную сумму и статус оплаты контракта на основе УСПЕШНЫХ платежей"""
    total_paid = contract.payments.filter(yookassa_status='succeeded').aggregate(total=models.Sum('amount'))['total'] or 0
    contract.paid_amount = total_paid
    contract.save()  # save() сам вызовет пересчет payment_status через метод модели

@receiver(post_save, sender=Payment)
def payment_saved(sender, instance, **kwargs):
    """При сохранении платежа обновляем контракт ТОЛЬКО для успешных платежей"""
    if instance.yookassa_status == 'succeeded':
        update_contract_payment_status(instance.contract)

@receiver(post_delete, sender=Payment)
def payment_deleted(sender, instance, **kwargs):
    """При удалении платежа обновляем контракт (удалённый платёж не должен учитываться)"""
    # При удалении платежа его статус не важен – его просто нет, поэтому пересчитываем всегда
    update_contract_payment_status(instance.contract)
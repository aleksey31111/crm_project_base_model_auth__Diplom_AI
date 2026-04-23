# contracts/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from .models import Payment, Contract
from django.db.models.signals import post_save
from django.dispatch import receiver
from contracts.models import Payment
from notifications.models import Notification
from tasks.models import extract_mentions

@receiver(post_save, sender=Payment)
def notify_mentions_in_payment_comment(sender, instance, created, **kwargs):
    if created and instance.comment:
        mentioned_users = extract_mentions(instance.comment)
        for user in mentioned_users:
            Notification.objects.create(
                user=user,
                type='info',
                title='Вас упомянули в комментарии к платежу',
                message=f'{instance.created_by.username} упомянул вас в платеже по контракту {instance.contract.number}: {instance.comment[:100]}',
                link=f'/contracts/{instance.contract.id}/'
            )

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
from django.db.models.signals import post_save
from django.dispatch import receiver
from tasks.models import Task
from contracts.models import Contract, Payment
from .models import TelegramUser
from .bot import send_telegram_notification

@receiver(post_save, sender=Task)
def task_notification(sender, instance, created, **kwargs):
    if created and instance.assigned_to:
        try:
            tg = TelegramUser.objects.get(user=instance.assigned_to, is_active=True)
            msg = f"📌 Новая задача: {instance.title}\nСрок: {instance.due_date}\nКонтракт: {instance.contract.number if instance.contract else '—'}"
            send_telegram_notification(tg.chat_id, msg)
        except TelegramUser.DoesNotExist:
            pass

@receiver(post_save, sender=Contract)
def contract_notification(sender, instance, created, **kwargs):
    if created and instance.manager:
        try:
            tg = TelegramUser.objects.get(user=instance.manager, is_active=True)
            msg = f"📄 Новый контракт: {instance.number}\nКлиент: {instance.client.full_name}\nСумма: {instance.amount}₽"
            send_telegram_notification(tg.chat_id, msg)
        except TelegramUser.DoesNotExist:
            pass

@receiver(post_save, sender=Payment)
def payment_notification(sender, instance, created, **kwargs):
    if instance.yookassa_status == 'succeeded' and instance.contract.manager:
        try:
            tg = TelegramUser.objects.get(user=instance.contract.manager, is_active=True)
            msg = f"✅ Успешная оплата по контракту {instance.contract.number}\nСумма: {instance.amount}₽"
            send_telegram_notification(tg.chat_id, msg)
        except TelegramUser.DoesNotExist:
            pass
from django.db.models.signals import post_save
from django.dispatch import receiver
from clients.models import Client
from contracts.models import Contract
from tasks.models import Task
from .models import Notification, NotificationPreference

def create_notification(user, title, message, notification_type='info', link=''):
    """Утилита для создания уведомления"""
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=notification_type,
        link=link
    )
    try:
        prefs = user.notification_prefs
        if prefs.email_enabled:
            # здесь можно вызвать send_email, но лучше через Celery
            pass
    except NotificationPreference.DoesNotExist:
        pass

# Клиенты
@receiver(post_save, sender=Client)
def client_created_notification(sender, instance, created, **kwargs):
    if created and instance.manager:
        create_notification(
            user=instance.manager,
            title=f'Новый клиент: {instance.full_name}',
            message=f'Клиент {instance.full_name} был добавлен в систему.',
            notification_type='success',
            link=f'/clients/{instance.id}/'
        )

# Контракты
@receiver(post_save, sender=Contract)
def contract_created_notification(sender, instance, created, **kwargs):
    if created and instance.manager:
        create_notification(
            user=instance.manager,
            title=f'Новый контракт: {instance.number}',
            message=f'Контракт с клиентом {instance.client.full_name} на сумму {instance.amount} руб.',
            notification_type='info',
            link=f'/contracts/{instance.id}/'
        )

# Задачи
@receiver(post_save, sender=Task)
def task_assigned_notification(sender, instance, created, **kwargs):
    if created and instance.assigned_to:
        create_notification(
            user=instance.assigned_to,
            title=f'Новая задача: {instance.title}',
            message=f'Вам назначена задача "{instance.title}". Срок: {instance.due_date}',
            notification_type='warning',
            link=f'/tasks/{instance.id}/'
        )
# tasks/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TaskComment, extract_mentions

### предотвратить появление "битых" ссылок в будущем ###
# tasks/signals.py

from django.db.models.signals import post_delete
from django.dispatch import receiver
from notifications.models import Notification
from .models import Task

@receiver(post_delete, sender=Task)
def delete_task_notifications(sender, instance, **kwargs):
    # Удаляем уведомления, у которых в поле link есть ссылка на эту задачу
    link_pattern = f'/tasks/{instance.pk}/'
    Notification.objects.filter(link__icontains=link_pattern).delete()

@receiver(post_save, sender=TaskComment)
def notify_mentions_in_task_comment(sender, instance, created, **kwargs):
    if created:
        mentioned_users = extract_mentions(instance.comment)
        for user in mentioned_users:
            Notification.objects.create(
                user=user,
                type='info',
                title='Вас упомянули в комментарии',
                message=f'{instance.created_by.username} упомянул вас в задаче "{instance.task.title}": {instance.comment[:100]}',
                link=f'/tasks/{instance.task.id}/'
            )
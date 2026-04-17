from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.models import Task
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Проверяет просроченные задачи и создаёт уведомления'

    def handle(self, *args, **options):
        now = timezone.now()
        overdue_tasks = Task.objects.filter(
            due_date__lt=now,
            status__in=['new', 'in_progress']
        ).select_related('assigned_to')

        created_count = 0
        for task in overdue_tasks:
            if task.assigned_to:
                # Создаём уведомление, если его ещё нет за сегодня (опционально)
                Notification.objects.get_or_create(
                    user=task.assigned_to,
                    type='warning',
                    title='Просрочена задача',
                    message=f'Задача "{task.title}" просрочена. Срок был {task.due_date.strftime("%d.%m.%Y %H:%M")}',
                    link=f'/tasks/{task.id}/'
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Создано {created_count} уведомлений о просроченных задачах.'))

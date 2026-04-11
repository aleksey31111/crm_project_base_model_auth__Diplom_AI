from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils import timezone
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Удаляет уведомления старше N дней'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Количество дней')

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - timedelta(days=days)
        old = Notification.objects.filter(created_at__lt=cutoff, is_read=True)
        count = old.count()
        old.delete()
        self.stdout.write(f'Удалено {count} уведомлений, созданных до {cutoff.date()}')
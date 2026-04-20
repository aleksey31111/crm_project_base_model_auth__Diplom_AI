# crm_project_base_model_auth/celery.py
import os
from celery import Celery
from celery.schedules import crontab


# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project_base_model_auth.settings')

app = Celery('crm_project_base_model_auth')

# Загружаем настройки из Django-конфигурации с префиксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим и регистрируем задачи из всех приложений Django
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'check-payment-status-hourly': {
        'task': 'contracts.tasks.check_payment_status',
        'schedule': crontab(minute=0, hour='*/1'),  # каждый час
    },
}

# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
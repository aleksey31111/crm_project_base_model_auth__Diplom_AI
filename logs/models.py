# logs/models.py
from django.db import models
from django.conf import settings
from core.models import TimeStampedModel   # <-- добавить эту строку

class APILog(TimeStampedModel):
    # ... остальной код без изменений
    class Direction(models.TextChoices):
        REQUEST = 'request', 'Запрос'
        RESPONSE = 'response', 'Ответ'
        WEBHOOK = 'webhook', 'Вебхук'

    direction = models.CharField(max_length=20, choices=Direction.choices, db_index=True)
    endpoint = models.CharField(max_length=255, blank=True, verbose_name='Эндпоинт')
    method = models.CharField(max_length=10, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    request_data = models.JSONField(default=dict, blank=True, verbose_name='Данные запроса')
    response_data = models.JSONField(default=dict, blank=True, verbose_name='Данные ответа')
    status_code = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Лог API'
        verbose_name_plural = 'Логи API'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_direction_display()} {self.endpoint} ({self.created_at})"

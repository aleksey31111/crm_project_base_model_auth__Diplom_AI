# core/signals.py

"""
Сигналы для core приложения.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save)
def log_pre_save(sender, instance, **kwargs):
    """Логирование перед сохранением"""
    if sender.__name__ not in ['LogEntry', 'Session']:
        logger.debug(f"Pre-save: {sender.__name__}")

@receiver(post_save)
def log_post_save(sender, instance, created, **kwargs):
    """Логирование после сохранения"""
    if sender.__name__ not in ['LogEntry', 'Session']:
        action = "created" if created else "updated"
        logger.info(f"{sender.__name__} {action}: {instance}")
# crm_project_base_model_auth/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
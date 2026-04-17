# client/task.py

from celery import shared_task

@shared_task
def test_task(message):
    print(f"Celery работает! Сообщение: {message}")
    return f"Обработано: {message}"
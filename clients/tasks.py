from celery import shared_task
import csv
import codecs
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from .models import Client
from accounts.models import User

@shared_task
def import_clients_from_csv(file_content, filename, user_id):
    """
    Фоновая задача импорта клиентов из CSV.
    file_content – содержимое файла в байтах.
    user_id – ID пользователя, инициировавшего импорт.
    """
    from django.core.exceptions import ValidationError
    from django.contrib.auth import get_user_model
    User = get_user_model()

    created_count = 0
    errors = []
    try:
        decoded = codecs.decode(file_content, 'utf-8-sig')
        reader = csv.DictReader(decoded.splitlines())
        # Ожидаем колонки: full_name, type, inn, phone, email, manager_username, status, ...
        with transaction.atomic():
            for row in reader:
                # Маппинг полей
                manager_username = row.get('manager_username', '').strip()
                manager = None
                if manager_username:
                    try:
                        manager = User.objects.get(username=manager_username)
                    except User.DoesNotExist:
                        errors.append(f"Менеджер {manager_username} не найден")
                        continue

                client_data = {
                    'full_name': row.get('full_name', '').strip(),
                    'type': row.get('type', 'individual'),
                    'inn': row.get('inn', '').strip(),
                    'phone': row.get('phone', '').strip(),
                    'email': row.get('email', '').strip(),
                    'status': row.get('status', 'active'),
                    'manager': manager,
                }
                # Дополнительные поля по желанию
                if not client_data['full_name']:
                    errors.append("Поле full_name обязательно")
                    continue

                client, created = Client.objects.get_or_create(
                    inn=client_data['inn'] if client_data['inn'] else None,
                    full_name=client_data['full_name'],
                    defaults=client_data
                )
                if created:
                    created_count += 1
                else:
                    errors.append(f"Клиент {client.full_name} уже существует")
    except Exception as e:
        errors.append(str(e))

    # Логируем результат (можно создать уведомление пользователю)
    return {
        'created': created_count,
        'errors': errors,
        'filename': filename
    }

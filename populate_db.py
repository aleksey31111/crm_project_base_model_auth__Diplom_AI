# populate_db.py
"""
Скрипт для заполнения базы данных тестовыми данными.
Запуск: python populate_db.py
"""

import os
import sys
import django
from datetime import timedelta, date
from decimal import Decimal

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project_base_model_auth1.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import UserProfile
from clients.models import Client
from contracts.models import Contract
from crm_project_base_model_auth1.crm_project_base_model_auth.tasks.models import Task, TaskComment
from analytics.models import Report
from notifications.models import Notification

User = get_user_model()


def create_users():
    """Создание пользователей"""
    print("\n📝 Создание пользователей...")

    users_data = [
        {
            'username': 'admin',
            'email': 'admin@crm_FAILED.ru',
            'password': 'admin123',
            'first_name': 'Админ',
            'last_name': 'Администратор',
            'is_superuser': True,
            'is_staff': True,
            'role': 'ADMIN',
            'phone': '+7 (999) 111-22-33',
            'position': 'Системный администратор',
            'department': 'IT',
            'hire_date': date(2023, 1, 15),
            'employee_id': 'EMP001'
        },
        {
            'username': 'ivanov',
            'email': 'ivanov@crm_FAILED.ru',
            'password': 'manager123',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'is_superuser': False,
            'is_staff': True,
            'role': 'MANAGER',
            'phone': '+7 (999) 222-33-44',
            'position': 'Ведущий менеджер',
            'department': 'Продажи',
            'hire_date': date(2023, 3, 10),
            'employee_id': 'EMP002'
        },
        {
            'username': 'petrov',
            'email': 'petrov@crm_FAILED.ru',
            'password': 'manager123',
            'first_name': 'Петр',
            'last_name': 'Петров',
            'is_superuser': False,
            'is_staff': True,
            'role': 'SALES',
            'phone': '+7 (999) 333-44-55',
            'position': 'Менеджер по продажам',
            'department': 'Продажи',
            'hire_date': date(2023, 5, 20),
            'employee_id': 'EMP003'
        },
        {
            'username': 'sidorova',
            'email': 'sidorova@crm_FAILED.ru',
            'password': 'support123',
            'first_name': 'Анна',
            'last_name': 'Сидорова',
            'is_superuser': False,
            'is_staff': True,
            'role': 'SUPPORT',
            'phone': '+7 (999) 444-55-66',
            'position': 'Специалист поддержки',
            'department': 'Поддержка',
            'hire_date': date(2023, 6, 5),
            'employee_id': 'EMP004'
        },
        {
            'username': 'smirnov',
            'email': 'smirnov@crm_FAILED.ru',
            'password': 'viewer123',
            'first_name': 'Алексей',
            'last_name': 'Смирнов',
            'is_superuser': False,
            'is_staff': True,
            'role': 'VIEWER',
            'phone': '+7 (999) 555-66-77',
            'position': 'Аналитик',
            'department': 'Аналитика',
            'hire_date': date(2023, 8, 1),
            'employee_id': 'EMP005'
        }
    ]

    created_users = []
    for data in users_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'is_superuser': data['is_superuser'],
                'is_staff': data['is_staff'],
                'role': data['role'],
                'phone': data['phone'],
                'position': data['position'],
                'department': data['department'],
                'hire_date': data['hire_date'],
                'employee_id': data['employee_id']
            }
        )
        if created:
            user.set_password(data['password'])
            user.save()
            print(f"  ✓ Создан пользователь: {user.get_full_name()} ({user.username})")
        else:
            print(f"  • Пользователь уже существует: {user.get_full_name()} ({user.username})")

        # Создаем профиль пользователя
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
            print(f"    - Создан профиль для {user.username}")

        created_users.append(user)

    return created_users


def create_clients():
    """Создание клиентов"""
    print("\n🏢 Создание клиентов...")

    # Получаем менеджеров
    managers = User.objects.filter(role__in=['ADMIN', 'MANAGER', 'SALES'])

    clients_data = [
        {
            'type': 'COMPANY',
            'full_name': 'ООО "Рога и Копыта"',
            'short_name': 'Рога и Копыта',
            'inn': '7701234567',
            'kpp': '770101001',
            'ogrn': '1027700123456',
            'phone': '+7 (495) 123-45-67',
            'email': 'info@roga.ru',
            'address': 'г. Москва, ул. Тверская, д. 10',
            'city': 'Москва',
            'country': 'Россия',
            'website': 'https://roga.ru',
            'status': 'active',
            'source': 'Сайт'
        },
        {
            'type': 'COMPANY',
            'full_name': 'АО "ТехноСервис"',
            'short_name': 'ТехноСервис',
            'inn': '7709876543',
            'kpp': '770102002',
            'ogrn': '1027700765432',
            'phone': '+7 (495) 987-65-43',
            'email': 'info@tehnoservice.ru',
            'address': 'г. Москва, ул. Ленина, д. 25',
            'city': 'Москва',
            'country': 'Россия',
            'website': 'https://tehnoservice.ru',
            'status': 'active',
            'source': 'Партнер'
        },
        {
            'type': 'INDIVIDUAL',
            'full_name': 'Петр Петрович Сидоров',
            'first_name': 'Петр',
            'last_name': 'Сидоров',
            'patronymic': 'Петрович',
            'birth_date': date(1985, 5, 15),
            'phone': '+7 (916) 123-45-67',
            'email': 'petrov@mail.ru',
            'address': 'г. Санкт-Петербург, Невский пр., д. 50, кв. 15',
            'city': 'Санкт-Петербург',
            'country': 'Россия',
            'status': 'active',
            'source': 'Реклама'
        },
        {
            'type': 'ENTREPRENEUR',
            'full_name': 'ИП Иванова Анна Сергеевна',
            'short_name': 'ИП Иванова',
            'inn': '123456789012',
            'ogrn': '304123456789012',
            'first_name': 'Анна',
            'last_name': 'Иванова',
            'patronymic': 'Сергеевна',
            'phone': '+7 (812) 456-78-90',
            'email': 'anna@ivanova.ru',
            'address': 'г. Санкт-Петербург, ул. Садовая, д. 10',
            'city': 'Санкт-Петербург',
            'country': 'Россия',
            'status': 'active',
            'source': 'Конференция'
        },
        {
            'type': 'COMPANY',
            'full_name': 'ООО "ИТ Решения"',
            'short_name': 'ИТ Решения',
            'inn': '5401234567',
            'kpp': '540101001',
            'ogrn': '1025401234567',
            'phone': '+7 (383) 777-88-99',
            'email': 'info@itsolutions.ru',
            'address': 'г. Новосибирск, ул. Советская, д. 15',
            'city': 'Новосибирск',
            'country': 'Россия',
            'website': 'https://itsolutions.ru',
            'status': 'lead',
            'source': 'Холодный звонок'
        },
        {
            'type': 'COMPANY',
            'full_name': 'ООО "СтройИнвест"',
            'short_name': 'СтройИнвест',
            'inn': '7812345678',
            'kpp': '781101001',
            'ogrn': '1027812345678',
            'phone': '+7 (812) 444-55-66',
            'email': 'contact@stroyinvest.ru',
            'address': 'г. Санкт-Петербург, пр. Невский, д. 100',
            'city': 'Санкт-Петербург',
            'country': 'Россия',
            'status': 'inactive',
            'source': 'Бывший клиент'
        }
    ]

    created_clients = []
    for i, data in enumerate(clients_data):
        # Назначаем менеджера по очереди
        manager = managers[i % len(managers)] if managers else None
        data['manager'] = manager

        client, created = Client.objects.get_or_create(
            inn=data.get('inn', f'TEMP_{i}'),
            defaults=data
        )
        if created:
            print(
                f"  ✓ Создан клиент: {client.full_name} (Менеджер: {client.manager.get_full_name() if client.manager else 'Не назначен'})")
        else:
            print(f"  • Клиент уже существует: {client.full_name}")
        created_clients.append(client)

    return created_clients


def create_contracts(clients):
    """Создание контрактов"""
    print("\n📄 Создание контрактов...")

    managers = User.objects.filter(role__in=['ADMIN', 'MANAGER', 'SALES'])

    contracts_data = [
        {
            'number': 'Д-001/2024',
            'title': 'Договор на поставку оборудования',
            'type': 'SALE',
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 12, 31),
            'amount': Decimal('1500000.00'),
            'paid_amount': Decimal('1500000.00'),
            'status': 'active'
        },
        {
            'number': 'Д-002/2024',
            'title': 'Договор на обслуживание',
            'type': 'MAINTENANCE',
            'start_date': date(2024, 2, 1),
            'end_date': date(2025, 1, 31),
            'amount': Decimal('500000.00'),
            'paid_amount': Decimal('250000.00'),
            'status': 'active'
        },
        {
            'number': 'Д-003/2024',
            'title': 'Консультационные услуги',
            'type': 'CONSULTING',
            'start_date': date(2024, 3, 1),
            'end_date': date(2024, 6, 30),
            'amount': Decimal('750000.00'),
            'paid_amount': Decimal('0'),
            'status': 'active'
        },
        {
            'number': 'Д-004/2024',
            'title': 'Аренда серверного оборудования',
            'type': 'LEASE',
            'start_date': date(2024, 1, 15),
            'end_date': date(2024, 7, 15),
            'amount': Decimal('300000.00'),
            'paid_amount': Decimal('150000.00'),
            'status': 'active'
        },
        {
            'number': 'Д-005/2024',
            'title': 'Разработка ПО',
            'type': 'SERVICE',
            'start_date': date(2024, 4, 1),
            'end_date': date(2024, 9, 30),
            'amount': Decimal('2000000.00'),
            'paid_amount': Decimal('500000.00'),
            'status': 'active'
        },
        {
            'number': 'Д-006/2024',
            'title': 'Техническая поддержка',
            'type': 'SERVICE',
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 6, 30),
            'amount': Decimal('250000.00'),
            'paid_amount': Decimal('250000.00'),
            'status': 'completed'
        }
    ]

    created_contracts = []
    for i, data in enumerate(contracts_data):
        client = clients[i % len(clients)]
        manager = managers[i % len(managers)] if managers else None

        contract, created = Contract.objects.get_or_create(
            number=data['number'],
            defaults={
                'client': client,
                'title': data['title'],
                'type': data['type'],
                'start_date': data['start_date'],
                'end_date': data['end_date'],
                'amount': data['amount'],
                'paid_amount': data['paid_amount'],
                'status': data['status'],
                'manager': manager
            }
        )

        if created:
            # Сохраняем для автоматического расчета статуса оплаты
            contract.save()
            print(f"  ✓ Создан контракт: {contract.number} - {contract.title} (Клиент: {client.full_name})")
        else:
            print(f"  • Контракт уже существует: {contract.number}")

        created_contracts.append(contract)

    return created_contracts


def create_tasks(clients, contracts):
    """Создание задач"""
    print("\n✅ Создание задач...")

    users = User.objects.all()

    tasks_data = [
        {
            'title': 'Подготовить коммерческое предложение',
            'description': 'Подготовить КП для клиента с учетом всех требований',
            'priority': 'HIGH',
            'due_date': timezone.now() + timedelta(days=3),
            'status': 'new'
        },
        {
            'title': 'Провести презентацию продукта',
            'description': 'Онлайн-презентация нового ПО для клиента',
            'priority': 'URGENT',
            'due_date': timezone.now() + timedelta(days=1),
            'status': 'in_progress'
        },
        {
            'title': 'Согласовать условия договора',
            'description': 'Согласовать финальные условия с юридическим отделом',
            'priority': 'HIGH',
            'due_date': timezone.now() + timedelta(days=5),
            'status': 'new'
        },
        {
            'title': 'Отправить счет на оплату',
            'description': 'Выставить счет по договору',
            'priority': 'MEDIUM',
            'due_date': timezone.now() + timedelta(days=2),
            'status': 'new'
        },
        {
            'title': 'Провести технический аудит',
            'description': 'Проверить инфраструктуру клиента',
            'priority': 'MEDIUM',
            'due_date': timezone.now() + timedelta(days=7),
            'status': 'new'
        },
        {
            'title': 'Подготовить отчетность',
            'description': 'Подготовить ежемесячный отчет по выполненным работам',
            'priority': 'LOW',
            'due_date': timezone.now() + timedelta(days=10),
            'status': 'new'
        },
        {
            'title': 'Провести обучение персонала',
            'description': 'Обучение работе с новым ПО',
            'priority': 'HIGH',
            'due_date': timezone.now() + timedelta(days=14),
            'status': 'new'
        },
        {
            'title': 'Настроить рабочую станцию',
            'description': 'Установить и настроить ПО для сотрудника',
            'priority': 'MEDIUM',
            'due_date': timezone.now() + timedelta(days=4),
            'status': 'in_progress'
        },
        {
            'title': 'Выполнить миграцию данных',
            'description': 'Перенос данных из старой системы',
            'priority': 'HIGH',
            'due_date': timezone.now() + timedelta(days=6),
            'status': 'new'
        },
        {
            'title': 'Провести анализ конкурентов',
            'description': 'Подготовить аналитику по рынку',
            'priority': 'LOW',
            'due_date': timezone.now() + timedelta(days=21),
            'status': 'new'
        }
    ]

    created_tasks = []
    for i, data in enumerate(tasks_data):
        client = clients[i % len(clients)]
        contract = contracts[i % len(contracts)] if contracts else None
        assigned_to = users[i % len(users)]

        task, created = Task.objects.get_or_create(
            title=data['title'],
            client=client,
            defaults={
                'description': data['description'],
                'contract': contract,
                'assigned_to': assigned_to,
                'priority': data['priority'],
                'due_date': data['due_date'],
                'status': data['status']
            }
        )

        if created:
            print(f"  ✓ Создана задача: {task.title} (Исполнитель: {task.assigned_to.get_full_name()})")
        else:
            print(f"  • Задача уже существует: {task.title}")

        created_tasks.append(task)

    return created_tasks


def create_task_comments(tasks):
    """Создание комментариев к задачам"""
    print("\n💬 Создание комментариев...")

    users = User.objects.all()

    comments_data = [
        "Начал работу над задачей. Ориентировочный срок - 2 дня.",
        "Согласовали все детали с клиентом. Работаем по плану.",
        "Возникли небольшие сложности, требуется дополнительное время.",
        "Задача выполнена на 80%. Осталось завершить документацию.",
        "Получил все необходимые данные. Приступаю к выполнению.",
        "Нужна консультация отдела разработки по данному вопросу.",
        "Отлично! Клиент доволен промежуточными результатами.",
        "Внес правки по замечаниям клиента. Жду подтверждения.",
        "Задача завершена. Отправил отчет клиенту.",
        "Перенес срок выполнения в связи с выходными."
    ]

    for i, task in enumerate(tasks[:8]):  # Добавляем комментарии к 8 задачам
        comment_count = 0
        for j in range(3):  # По 3 комментария на задачу
            user = users[(i + j) % len(users)]
            comment_text = comments_data[(i + j) % len(comments_data)]

            comment, created = TaskComment.objects.get_or_create(
                task=task,
                comment=comment_text,
                created_by=user,
                defaults={
                    'comment': comment_text,
                    'created_by': user
                }
            )
            if created:
                comment_count += 1

        if comment_count > 0:
            print(f"  ✓ Добавлено {comment_count} комментариев к задаче: {task.title}")


def create_reports():
    """Создание отчетов"""
    print("\n📊 Создание отчетов...")

    users = User.objects.all()

    reports_data = [
        {
            'name': 'Отчет по продажам за январь',
            'type': 'SALES',
            'format': 'EXCEL',
            'parameters': {'period': '2024-01', 'department': 'sales'}
        },
        {
            'name': 'Анализ клиентской базы',
            'type': 'CLIENTS',
            'format': 'EXCEL',
            'parameters': {'status': 'active', 'type': 'company'}
        },
        {
            'name': 'Отчет по выполненным задачам',
            'type': 'TASKS',
            'format': 'PDF',
            'parameters': {'period': '2024-Q1', 'status': 'completed'}
        },
        {
            'name': 'Финансовый отчет по контрактам',
            'type': 'CONTRACTS',
            'format': 'EXCEL',
            'parameters': {'year': 2024, 'status': 'active'}
        }
    ]

    for i, data in enumerate(reports_data):
        user = users[i % len(users)]

        report, created = Report.objects.get_or_create(
            name=data['name'],
            defaults={
                'type': data['type'],
                'format': data['format'],
                'parameters': data['parameters'],
                'created_by': user
            }
        )

        if created:
            print(f"  ✓ Создан отчет: {report.name}")
        else:
            print(f"  • Отчет уже существует: {report.name}")


def create_notifications():
    """Создание уведомлений"""
    print("\n🔔 Создание уведомлений...")

    users = User.objects.all()

    notifications_data = [
        {'type': 'INFO', 'title': 'Новая задача',
         'message': 'Вам назначена новая задача "Подготовить коммерческое предложение"'},
        {'type': 'SUCCESS', 'title': 'Задача выполнена', 'message': 'Задача "Провести презентацию" успешно выполнена'},
        {'type': 'WARNING', 'title': 'Скоро истекает срок',
         'message': 'Срок выполнения задачи "Согласовать условия" истекает через 2 дня'},
        {'type': 'ERROR', 'title': 'Ошибка в системе', 'message': 'Не удалось отправить отчет. Попробуйте позже'},
        {'type': 'INFO', 'title': 'Новый контракт',
         'message': 'Подписан новый контракт с клиентом ООО "Рога и Копыта"'},
        {'type': 'SUCCESS', 'title': 'Оплата получена', 'message': 'Поступила оплата по договору №Д-001/2024'},
        {'type': 'WARNING', 'title': 'Просроченная задача', 'message': 'Задача "Провести обучение" просрочена'},
        {'type': 'INFO', 'title': 'Комментарий к задаче',
         'message': 'Пользователь Иван Иванов оставил комментарий к вашей задаче'}
    ]

    for i, user in enumerate(users):
        # Создаем по 3 уведомления для каждого пользователя
        for j in range(3):
            data = notifications_data[(i + j) % len(notifications_data)]
            notification, created = Notification.objects.get_or_create(
                user=user,
                title=data['title'],
                defaults={
                    'type': data['type'],
                    'message': data['message'],
                    'is_read': j == 0,  # Первое уведомление прочитано
                    'read_at': timezone.now() if j == 0 else None
                }
            )

            if created:
                print(f"  ✓ Создано уведомление для {user.username}: {notification.title}")

    print(f"\n  Всего создано уведомлений: {Notification.objects.count()}")


def main():
    """Главная функция"""
    print("=" * 60)
    print("🚀 ЗАПОЛНЕНИЕ БАЗЫ ДАННЫХ CRM")
    print("=" * 60)

    try:
        # Создаем все данные
        users = create_users()
        clients = create_clients()
        contracts = create_contracts(clients)
        tasks = create_tasks(clients, contracts)
        create_task_comments(tasks)
        create_reports()
        create_notifications()

        # Выводим статистику
        print("\n" + "=" * 60)
        print("📊 СТАТИСТИКА ЗАПОЛНЕНИЯ")
        print("=" * 60)
        print(f"👥 Пользователей: {User.objects.count()}")
        print(f"🏢 Клиентов: {Client.objects.count()}")
        print(f"📄 Контрактов: {Contract.objects.count()}")
        print(f"✅ Задач: {Task.objects.count()}")
        print(f"💬 Комментариев: {TaskComment.objects.count()}")
        print(f"📊 Отчетов: {Report.objects.count()}")
        print(f"🔔 Уведомлений: {Notification.objects.count()}")

        # Суммы контрактов
        total_amount = Contract.objects.aggregate(total=models.Sum('amount'))['total'] or 0
        total_paid = Contract.objects.aggregate(total=models.Sum('paid_amount'))['total'] or 0
        print(f"\n💰 Общая сумма контрактов: {total_amount:,.2f} ₽")
        print(f"💵 Оплачено: {total_paid:,.2f} ₽")
        print(f"💳 Остаток: {total_amount - total_paid:,.2f} ₽")

        print("\n" + "=" * 60)
        print("✅ БАЗА ДАННЫХ УСПЕШНО ЗАПОЛНЕНА!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    # Импортируем models для агрегации
    import django.db.models as models

    main()
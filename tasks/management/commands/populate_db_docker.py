######## populate_db_docker #########
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random
import uuid

from accounts.models import UserProfile
from clients.models import Client
from contracts.models import Contract, Payment
from tasks.models import Task, TaskComment
from analytics.models import Report
from notifications.models import Notification, NotificationPreference

User = get_user_model()


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными для Docker-окружения'

    def handle(self, *args, **options):
        self.stdout.write("Начало заполнения тестовыми данными...")

        # 1. Создание пользователей
        users = self.create_users()

        # 2. Создание клиентов
        clients = self.create_clients(users)

        # 3. Создание контрактов
        contracts = self.create_contracts(clients, users)

        # 4. Создание платежей
        self.create_payments(contracts, users)

        # 5. Создание задач
        tasks = self.create_tasks(clients, contracts, users)

        # 6. Создание комментариев к задачам
        self.create_task_comments(tasks, users)

        # 7. Создание отчётов
        self.create_reports(users)

        # 8. Создание уведомлений и настроек
        self.create_notifications_and_prefs(users)

        self.stdout.write(self.style.SUCCESS("База данных успешно заполнена!"))

    # ----------------------------------------------------------------------
    # Пользователи
    # ----------------------------------------------------------------------
    def create_users(self):
        users_data = [
            {
                'username': 'admin', 'email': 'admin@crm.ru', 'password': 'admin123',
                'first_name': 'Админ', 'last_name': 'Администратор', 'role': 'ADMIN',
                'is_superuser': True, 'is_staff': True, 'phone': '+7 (999) 111-22-33',
                'position': 'Системный администратор', 'department': 'IT',
                'hire_date': date(2023, 1, 15), 'employee_id': 'EMP001'
            },
            {
                'username': 'ivanov', 'email': 'ivanov@crm.ru', 'password': 'manager123',
                'first_name': 'Иван', 'last_name': 'Иванов', 'role': 'MANAGER',
                'phone': '+7 (999) 222-33-44', 'position': 'Ведущий менеджер',
                'department': 'Продажи', 'hire_date': date(2023, 3, 10), 'employee_id': 'EMP002'
            },
            {
                'username': 'petrov', 'email': 'petrov@crm.ru', 'password': 'manager123',
                'first_name': 'Петр', 'last_name': 'Петров', 'role': 'SALES',
                'phone': '+7 (999) 333-44-55', 'position': 'Менеджер по продажам',
                'department': 'Продажи', 'hire_date': date(2023, 5, 20), 'employee_id': 'EMP003'
            },
            {
                'username': 'sidorova', 'email': 'sidorova@crm.ru', 'password': 'support123',
                'first_name': 'Анна', 'last_name': 'Сидорова', 'role': 'SUPPORT',
                'phone': '+7 (999) 444-55-66', 'position': 'Специалист поддержки',
                'department': 'Поддержка', 'hire_date': date(2023, 6, 5), 'employee_id': 'EMP004'
            },
            {
                'username': 'smirnov', 'email': 'smirnov@crm.ru', 'password': 'viewer123',
                'first_name': 'Алексей', 'last_name': 'Смирнов', 'role': 'VIEWER',
                'phone': '+7 (999) 555-66-77', 'position': 'Аналитик',
                'department': 'Аналитика', 'hire_date': date(2023, 8, 1), 'employee_id': 'EMP005'
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
                    'role': data['role'],
                    'is_superuser': data.get('is_superuser', False),
                    'is_staff': data.get('is_staff', False),
                    'phone': data.get('phone', ''),
                    'position': data.get('position', ''),
                    'department': data.get('department', ''),
                    'hire_date': data.get('hire_date'),
                    'employee_id': data.get('employee_id')
                }
            )
            if created:
                user.set_password(data['password'])
                user.save()
                self.stdout.write(f"  Создан пользователь: {user.username} ({user.get_role_display()})")
            else:
                self.stdout.write(f"  Пользователь {user.username} уже существует")

            # Создаём профиль, если нет
            UserProfile.objects.get_or_create(user=user)
            created_users.append(user)
        return created_users

    # ----------------------------------------------------------------------
    # Клиенты
    # ----------------------------------------------------------------------
    def create_clients(self, users):
        managers = [u for u in users if u.role in ['ADMIN', 'MANAGER', 'SALES']]
        clients_data = [
            {
                'type': 'company', 'full_name': 'ООО "Рога и Копыта"', 'short_name': 'Рога и Копыта',
                'inn': '7701234567', 'kpp': '770101001', 'ogrn': '1027700123456',
                'phone': '+7 (495) 123-45-67', 'email': 'info@roga.ru',
                'country': 'Россия', 'city': 'Москва', 'address': 'ул. Тверская, д. 10',
                'status': 'active', 'source': 'Сайт'
            },
            {
                'type': 'company', 'full_name': 'АО "ТехноСервис"', 'short_name': 'ТехноСервис',
                'inn': '7709876543', 'kpp': '770102002', 'ogrn': '1027700765432',
                'phone': '+7 (495) 987-65-43', 'email': 'info@tehnoservice.ru',
                'country': 'Россия', 'city': 'Москва', 'address': 'ул. Ленина, д. 25',
                'status': 'active', 'source': 'Партнер'
            },
            {
                'type': 'individual', 'full_name': 'Петр Петрович Сидоров',
                'first_name': 'Петр', 'last_name': 'Сидоров', 'patronymic': 'Петрович',
                'birth_date': date(1985, 5, 15), 'phone': '+7 (916) 123-45-67',
                'email': 'petrov@mail.ru', 'country': 'Россия', 'city': 'Санкт-Петербург',
                'address': 'Невский пр., д. 50, кв. 15', 'status': 'active', 'source': 'Реклама'
            },
            {
                'type': 'entrepreneur', 'full_name': 'ИП Иванова Анна Сергеевна',
                'short_name': 'ИП Иванова', 'inn': '123456789012', 'ogrn': '304123456789012',
                'first_name': 'Анна', 'last_name': 'Иванова', 'patronymic': 'Сергеевна',
                'phone': '+7 (812) 456-78-90', 'email': 'anna@ivanova.ru',
                'country': 'Россия', 'city': 'Санкт-Петербург', 'address': 'ул. Садовая, д. 10',
                'status': 'active', 'source': 'Конференция'
            },
            {
                'type': 'company', 'full_name': 'ООО "ИТ Решения"', 'short_name': 'ИТ Решения',
                'inn': '5401234567', 'kpp': '540101001', 'ogrn': '1025401234567',
                'phone': '+7 (383) 777-88-99', 'email': 'info@itsolutions.ru',
                'country': 'Россия', 'city': 'Новосибирск', 'address': 'ул. Советская, д. 15',
                'status': 'lead', 'source': 'Холодный звонок'
            },
            {
                'type': 'company', 'full_name': 'ООО "СтройИнвест"', 'short_name': 'СтройИнвест',
                'inn': '7812345678', 'kpp': '781101001', 'ogrn': '1027812345678',
                'phone': '+7 (812) 444-55-66', 'email': 'contact@stroyinvest.ru',
                'country': 'Россия', 'city': 'Санкт-Петербург', 'address': 'пр. Невский, д. 100',
                'status': 'inactive', 'source': 'Бывший клиент'
            }
        ]
        clients = []
        for i, data in enumerate(clients_data):
            manager = managers[i % len(managers)] if managers else None
            client, created = Client.objects.get_or_create(
                inn=data.get('inn', f'TEMP_{i}'),  # Для физлиц без ИНН используем уникальный ключ
                defaults={
                    'type': data['type'], 'full_name': data['full_name'],
                    'short_name': data.get('short_name', ''),
                    'kpp': data.get('kpp', ''), 'ogrn': data.get('ogrn', ''),
                    'first_name': data.get('first_name', ''), 'last_name': data.get('last_name', ''),
                    'patronymic': data.get('patronymic', ''), 'birth_date': data.get('birth_date'),
                    'phone': data['phone'], 'email': data.get('email', ''),
                    'country': data.get('country', ''), 'city': data.get('city', ''),
                    'address': data.get('address', ''), 'status': data['status'],
                    'source': data.get('source', ''), 'manager': manager
                }
            )
            if created:
                self.stdout.write(
                    f"  Создан клиент: {client.full_name} (менеджер: {client.manager.username if client.manager else '—'})")
            else:
                self.stdout.write(f"  Клиент {client.full_name} уже существует")
            clients.append(client)
        return clients

    # ----------------------------------------------------------------------
    # Контракты
    # ----------------------------------------------------------------------
    def create_contracts(self, clients, users):
        managers = [u for u in users if u.role in ['ADMIN', 'MANAGER', 'SALES']]
        contracts_data = [
            {'number': 'Д-001/2024', 'title': 'Поставка оборудования', 'type': 'sale',
             'amount': 1500000, 'paid_amount': 1500000, 'status': 'active', 'payment_status': 'paid',
             'start_date': date(2024, 1, 1), 'end_date': date(2024, 12, 31)},
            {'number': 'Д-002/2024', 'title': 'Обслуживание ПО', 'type': 'maintenance',
             'amount': 500000, 'paid_amount': 250000, 'status': 'active', 'payment_status': 'partially_paid',
             'start_date': date(2024, 2, 1), 'end_date': date(2025, 1, 31)},
            {'number': 'Д-003/2024', 'title': 'Консультационные услуги', 'type': 'consulting',
             'amount': 750000, 'paid_amount': 0, 'status': 'active', 'payment_status': 'not_paid',
             'start_date': date(2024, 3, 1), 'end_date': date(2024, 6, 30)},
            {'number': 'Д-004/2024', 'title': 'Аренда серверов', 'type': 'lease',
             'amount': 300000, 'paid_amount': 150000, 'status': 'active', 'payment_status': 'partially_paid',
             'start_date': date(2024, 1, 15), 'end_date': date(2024, 7, 15)},
            {'number': 'Д-005/2024', 'title': 'Разработка CRM', 'type': 'service',
             'amount': 2000000, 'paid_amount': 500000, 'status': 'active', 'payment_status': 'partially_paid',
             'start_date': date(2024, 4, 1), 'end_date': date(2024, 9, 30)},
            {'number': 'Д-006/2024', 'title': 'Техподдержка', 'type': 'service',
             'amount': 250000, 'paid_amount': 250000, 'status': 'completed', 'payment_status': 'paid',
             'start_date': date(2024, 1, 1), 'end_date': date(2024, 6, 30)},
            {'number': 'Д-007/2025', 'title': 'Обновление инфраструктуры', 'type': 'sale',
             'amount': 800000, 'paid_amount': 0, 'status': 'active', 'payment_status': 'not_paid',
             'start_date': date(2025, 2, 10), 'end_date': date(2025, 11, 30)},
        ]
        contracts = []
        for i, data in enumerate(contracts_data):
            client = clients[i % len(clients)]
            manager = managers[i % len(managers)] if managers else None
            contract, created = Contract.objects.get_or_create(
                number=data['number'],
                defaults={
                    'client': client, 'title': data['title'], 'type': data['type'],
                    'amount': data['amount'], 'paid_amount': data['paid_amount'],
                    'status': data['status'], 'payment_status': data['payment_status'],
                    'start_date': data['start_date'], 'end_date': data['end_date'],
                    'signed_date': data['start_date'], 'manager': manager
                }
            )
            # if created:
            #     # Для учебных целей добавляем имитацию платёжной ссылки для неоплаченных контрактов
            #     if contract.payment_status != 'paid':
            #         fake_id = f"fake_{uuid.uuid4().hex[:10]}"
            #         contract.yookassa_payment_id = fake_id
            #         contract.payment_url = f"/fake-payment/{contract.id}/?amount={contract.remaining_amount}"
            #         contract.save(update_fields=['yookassa_payment_id', 'payment_url'])
            #         Payment.objects.get_or_create(
            #             contract=contract,
            #             yookassa_id=fake_payment_id,
            #             defaults={
            #                 'amount': contract.remaining_amount,
            #                 'payment_date': contract.start_date,
            #                 'payment_method': 'card',
            #                 'yookassa_status': 'pending',
            #                 'confirmation_url': fake_confirmation_url,
            #                 'comment': f'Автоматический платёж для контракта {contract.number}'
            #             }
            #         )
            #     self.stdout.write(f"  Создан контракт: {contract.number} ({contract.client.full_name})")
            if created:
                # Для учебных целей добавляем имитацию платёжной ссылки для неоплаченных контрактов
                if contract.payment_status != 'paid':
                    fake_id = f"fake_{uuid.uuid4().hex[:10]}"
                    fake_url = f"/fake-payment/{contract.id}/?amount={contract.remaining_amount}"
                    contract.yookassa_payment_id = fake_id
                    contract.payment_url = fake_url
                    contract.save(update_fields=['yookassa_payment_id', 'payment_url'])
                    # Обязательно создаём запись Payment, чтобы вебхук мог её найти
                    Payment.objects.get_or_create(
                        contract=contract,
                        yookassa_id=fake_id,
                        defaults={
                            'amount': contract.remaining_amount,
                            'payment_date': timezone.now().date(),
                            'payment_method': 'card',
                            'yookassa_status': 'pending',
                            'confirmation_url': fake_url,
                            'comment': f'Автоматический платёж для контракта {contract.number}'
                        }
                    )
                self.stdout.write(f"  Создан контракт: {contract.number} ({contract.client.full_name})")
            else:
                self.stdout.write(f"  Контракт {contract.number} уже существует")
            contracts.append(contract)
        return contracts

    # ----------------------------------------------------------------------
    # Платежи
    # ----------------------------------------------------------------------
    def create_payments(self, contracts, users):
        payment_methods = ['bank_transfer', 'card', 'cash', 'electronic']
        for contract in contracts:
            # Если контракт частично оплачен, добавляем несколько платежей
            if contract.payment_status == 'partially_paid':
                # Создаём 1-2 платежа
                amounts = [contract.amount * Decimal('0.3'), contract.amount * Decimal('0.2')]
                for amount in amounts:
                    if amount > 0:
                        pay_date = contract.start_date + timedelta(days=random.randint(1, 30))
                        payment, created = Payment.objects.get_or_create(
                            contract=contract,
                            amount=amount,
                            payment_date=pay_date,
                            defaults={
                                'payment_method': random.choice(payment_methods),
                                'comment': 'Тестовый платёж',
                                'created_by': random.choice(users),
                                'yookassa_status': 'succeeded',
                                'paid_at': timezone.now()
                            }
                        )
                        if created:
                            self.stdout.write(f"    Добавлен платёж {amount} руб. для контракта {contract.number}")
            elif contract.payment_status == 'paid' and not Payment.objects.filter(contract=contract).exists():
                # Добавляем один платёж на полную сумму
                payment, created = Payment.objects.get_or_create(
                    contract=contract,
                    amount=contract.amount,
                    payment_date=contract.start_date,
                    defaults={
                        'payment_method': random.choice(payment_methods),
                        'comment': 'Полная оплата',
                        'created_by': random.choice(users),
                        'yookassa_status': 'succeeded',
                        'paid_at': timezone.now()
                    }
                )
                if created:
                    self.stdout.write(
                        f"    Добавлен платёж {contract.amount} руб. (полная оплата) для контракта {contract.number}")

    # ----------------------------------------------------------------------
    # Задачи
    # ----------------------------------------------------------------------
    def create_tasks(self, clients, contracts, users):
        tasks_data = [
            {'title': 'Подготовить коммерческое предложение', 'priority': 'high', 'status': 'new',
             'due_offset': 3, 'client_idx': 0, 'contract_idx': 0},
            {'title': 'Провести презентацию продукта', 'priority': 'urgent', 'status': 'in_progress',
             'due_offset': 1, 'client_idx': 1, 'contract_idx': 1},
            {'title': 'Согласовать условия договора', 'priority': 'high', 'status': 'new',
             'due_offset': 5, 'client_idx': 2, 'contract_idx': 2},
            {'title': 'Отправить счёт на оплату', 'priority': 'medium', 'status': 'new',
             'due_offset': 2, 'client_idx': 3, 'contract_idx': 3},
            {'title': 'Провести технический аудит', 'priority': 'medium', 'status': 'new',
             'due_offset': 7, 'client_idx': 4, 'contract_idx': 4},
            {'title': 'Подготовить отчётность', 'priority': 'low', 'status': 'new',
             'due_offset': 10, 'client_idx': 5, 'contract_idx': 5},
            {'title': 'Обучение персонала', 'priority': 'high', 'status': 'new',
             'due_offset': 14, 'client_idx': 0, 'contract_idx': 0},
            {'title': 'Настройка рабочей станции', 'priority': 'medium', 'status': 'in_progress',
             'due_offset': 4, 'client_idx': 1, 'contract_idx': 1},
            {'title': 'Миграция данных', 'priority': 'high', 'status': 'new',
             'due_offset': 6, 'client_idx': 2, 'contract_idx': 2},
            {'title': 'Анализ конкурентов', 'priority': 'low', 'status': 'new',
             'due_offset': 21, 'client_idx': 3, 'contract_idx': 3},
            {'title': 'Просроченная задача - срочно', 'priority': 'urgent', 'status': 'in_progress',
             'due_offset': -5, 'client_idx': 4, 'contract_idx': 4},
        ]
        tasks = []
        now = timezone.now()
        for i, data in enumerate(tasks_data):
            client = clients[data['client_idx'] % len(clients)]
            contract = contracts[data['contract_idx'] % len(contracts)] if contracts else None
            assigned_to = users[i % len(users)]
            due_date = now + timedelta(days=data['due_offset']) if data['due_offset'] >= 0 else now + timedelta(
                days=data['due_offset'])
            task, created = Task.objects.get_or_create(
                title=data['title'],
                client=client,
                defaults={
                    'description': f'Детали задачи: {data["title"]}',
                    'contract': contract,
                    'assigned_to': assigned_to,
                    'priority': data['priority'],
                    'status': data['status'],
                    'due_date': due_date,
                    'estimated_hours': Decimal(random.randint(2, 20)),
                    'actual_hours': Decimal(random.randint(0, 15)) if data['status'] == 'completed' else None
                }
            )
            if created:
                self.stdout.write(f"  Создана задача: {task.title} (исполнитель: {task.assigned_to.username})")
            else:
                self.stdout.write(f"  Задача {task.title} уже существует")
            tasks.append(task)
        return tasks

    # ----------------------------------------------------------------------
    # Комментарии к задачам
    # ----------------------------------------------------------------------
    def create_task_comments(self, tasks, users):
        comments = [
            "Начал работу над задачей. Ориентировочный срок - 2 дня.",
            "Согласовали все детали с клиентом. Работаем по плану.",
            "Возникли небольшие сложности, требуется дополнительное время.",
            "Задача выполнена на 80%. Осталось завершить документацию.",
            "Получил все необходимые данные. Приступаю к выполнению.",
            "Нужна консультация отдела разработки.",
            "Отлично! Клиент доволен промежуточными результатами.",
            "Внёс правки по замечаниям клиента. Жду подтверждения.",
            "Задача завершена. Отправил отчёт клиенту."
        ]
        for task in tasks[:8]:  # первые 8 задач
            for j in range(2):  # по 2 комментария
                comment_text = comments[(task.id + j) % len(comments)]
                user = users[(task.id + j) % len(users)]
                comment, created = TaskComment.objects.get_or_create(
                    task=task,
                    comment=comment_text,
                    created_by=user,
                    defaults={'comment': comment_text}
                )
                if created:
                    self.stdout.write(f"    Добавлен комментарий к задаче {task.title}")

    # ----------------------------------------------------------------------
    # Отчёты
    # ----------------------------------------------------------------------
    def create_reports(self, users):
        reports_data = [
            {'name': 'Отчёт по продажам за январь', 'type': 'sales', 'format': 'excel',
             'parameters': {'period': '2024-01', 'department': 'sales'}},
            {'name': 'Анализ клиентской базы', 'type': 'clients', 'format': 'excel',
             'parameters': {'status': 'active', 'type': 'company'}},
            {'name': 'Отчёт по выполненным задачам', 'type': 'tasks', 'format': 'pdf',
             'parameters': {'period': '2024-Q1', 'status': 'completed'}},
            {'name': 'Финансовый отчёт по контрактам', 'type': 'contracts', 'format': 'excel',
             'parameters': {'year': 2024, 'status': 'active'}},
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
                self.stdout.write(f"  Создан отчёт: {report.name}")

    # ----------------------------------------------------------------------
    # Уведомления и настройки уведомлений
    # ----------------------------------------------------------------------
    def create_notifications_and_prefs(self, users):
        # Создаём NotificationPreference для каждого пользователя, если нет
        for user in users:
            prefs, created = NotificationPreference.objects.get_or_create(user=user)
            if created:
                self.stdout.write(f"  Созданы настройки уведомлений для {user.username}")

        # Создаём уведомления
        notifications_data = [
            {'type': 'info', 'title': 'Новая задача',
             'message': 'Вам назначена задача "Подготовить коммерческое предложение"'},
            {'type': 'success', 'title': 'Задача выполнена',
             'message': 'Задача "Провести презентацию" успешно выполнена'},
            {'type': 'warning', 'title': 'Скоро истекает срок',
             'message': 'Срок выполнения задачи "Согласовать условия" истекает через 2 дня'},
            {'type': 'error', 'title': 'Ошибка в системе', 'message': 'Не удалось отправить отчёт. Попробуйте позже'},
            {'type': 'info', 'title': 'Новый контракт', 'message': 'Подписан новый контракт с ООО "Рога и Копыта"'},
            {'type': 'success', 'title': 'Оплата получена', 'message': 'Поступила оплата по договору №Д-001/2024'},
            {'type': 'warning', 'title': 'Просроченная задача', 'message': 'Задача "Обучение персонала" просрочена'},
        ]
        for i, user in enumerate(users):
            # По 2-3 уведомления на пользователя
            for j in range(3):
                data = notifications_data[(i + j) % len(notifications_data)]
                notif, created = Notification.objects.get_or_create(
                    user=user,
                    title=data['title'],
                    defaults={
                        'type': data['type'],
                        'message': data['message'],
                        'is_read': j == 0  # первое уведомление прочитано
                    }
                )
                if created:
                    self.stdout.write(f"  Создано уведомление для {user.username}: {notif.title}")
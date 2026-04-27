CRM-система для управления клиентами, контрактами и задачами
Учебный проект, демонстрирующий построение корпоративной CRM с использованием Django, Django REST Framework, Celery, PostgreSQL, Redis и Docker. Реализованы: аутентификация, ролевая модель, управление клиентами и контрактами, задачи с канбан-доской, аналитика, экспорт/импорт данных, уведомления и имитация платежей.

📋 Оглавление
Возможности
Технологии
Установка и запуск
Через Docker (рекомендуется)
Локально без Docker
Настройка переменных окружения
Имитация платежей (учебный режим)
Экспорт и импорт данных
Управляющие команды
Тестирование
Логирование
Структура проекта
Возможные проблемы и решения
Лицензия
🚀 Возможности
Аутентификация и роли: регистрация, вход, сброс пароля. Роли: администратор, менеджер, продажник, поддержка, наблюдатель.
Управление клиентами: CRUD, типы (юр. лицо, физ. лицо, ИП), контактная информация, ответственный менеджер.
Контракты: номера, суммы, статусы оплаты, привязка к клиентам и менеджерам. Ручное добавление оплат.
Задачи: назначение, приоритеты, сроки, комментарии, канбан-доска (drag‑and‑drop).
Аналитика: дашборд с графиками выручки, статусов задач, виджеты статистики.
Уведомления: внутренние, с настройками (email/telegram), отметка о прочтении.
Экспорт в Excel: клиенты, контракты, задачи, платежи (библиотека openpyxl).
Импорт клиентов из CSV через фоновую задачу Celery.
Имитация платежей (учебный режим): фейковая страница оплаты, ручное подтверждение через админку.
Docker‑окружение: Django, PostgreSQL, Redis, Celery, Nginx.
REST API: авторизация JWT, документация Swagger, фильтрация, пагинация.
Логирование: запись в файл и в БД (модель APILog).
🛠 Технологии
Backend: Python 3.12, Django 4.2, Django REST Framework, Celery
База данных: PostgreSQL 15 (или SQLite для разработки)
Кеш/брокер: Redis
Веб-сервер: Gunicorn + Nginx (в продакшене)
Контейнеризация: Docker, Docker Compose
Платежи (учебные): собственная имитация (без реальной ЮKassa)
Экспорт: openpyxl
Логирование: стандартный logging + кастомная модель
⚙️ Установка и запуск
Через Docker (рекомендуется)
Клонируйте репозиторий

#git clone https://github.com/your-username/crm_project_base_model_auth.git
cd crm_project_base_model_auth
Создайте файл .env (см. раздел Настройка переменных окружения)

Соберите и запустите контейнеры

docker-compose up -d --build
Выполните миграции и соберите статику

docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
Создайте суперпользователя

docker-compose exec web python manage.py createsuperuser
Откройте в браузере

Проект: http://localhost (или порт, указанный в docker-compose.yml)
Админка: http://localhost/admin
API документация: http://localhost/api/docs/
Остановка

docker-compose down
Локально без Docker
Установите Python 3.12 и создайте виртуальное окружение:

#python -m venv .venv
#source .venv/bin/activate  # Linux/Mac
#.venv\Scripts\activate      # Windows
Установите зависимости:

pip install -r requirements.txt
Установите и настройте PostgreSQL (или используйте SQLite). Пример для PostgreSQL:

Создайте БД и пользователя.
Укажите параметры в .env.
Выполните миграции:

python manage.py migrate
Создайте суперпользователя:

python manage.py createsuperuser
Запустите сервер:

python manage.py runserver
Запустите Celery (в отдельном терминале):

celery -A crm_project_base_model_auth worker -l info
celery -A crm_project_base_model_auth beat -l info
🔐 Настройка переменных окружения
Создайте файл .env в корне проекта со следующим содержимым:

# Django
SECRET_KEY=your-secret-key-here
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# База данных (для Docker используйте имена сервисов)
DB_NAME=crm_db
DB_USER=crm_user
DB_PASSWORD=crm_password
DB_HOST=db          # для Docker, для локального - localhost
DB_PORT=5432

# Redis (для Celery)
REDIS_URL=redis://redis:6379/0   # для Docker
# REDIS_URL=redis://localhost:6379/0   # для локального запуска

# Базовый URL (для ссылок в письмах и возврата после оплаты)
BASE_URL=http://localhost:8000

# Платежи (для учебного режима оставьте пустыми)
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=

# Email (опционально)
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email@yandex.ru
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@yandex.ru
Важно: Никогда не коммитьте .env в репозиторий. Добавьте его в .gitignore.

💳 Имитация платежей (учебный режим)
Поскольку для регистрации в ЮKassa требуется ИНН, в проекте реализована полная имитация процесса оплаты:

На странице контракта появляется кнопка «Оплатить (тест)».
При нажатии открывается фейковая платёжная страница (без реального API).
Пользователь нажимает «Подтвердить оплату», после чего отправляется запрос на внутренний вебхук, который обновляет статус контракта на «Оплачен».
Ручное управление: в админке Django для контракта есть действие «Имитировать успешную оплату» – создаёт платёж на всю сумму и помечает контракт оплаченным.
Внимание: Никакие реальные деньги не списываются. Вся логика существует только для демонстрации работы платёжного модуля.

📊 Экспорт и импорт данных
Экспорт в Excel
На страницах списков (клиенты, контракты, задачи, платежи) добавлена кнопка «Экспорт Excel».
Файл генерируется через библиотеку openpyxl и содержит все поля сущности с заголовками.

Импорт клиентов из CSV
На странице списка клиентов нажмите «Импорт CSV».
Загрузите файл с колонками (первая строка – заголовки):
full_name (обязательно)
type (individual/company/entrepreneur)
inn, phone, email, status (active/inactive/lead)
manager_username – имя пользователя-менеджера (должен существовать)
Импорт выполняется асинхронно через Celery. Результат можно увидеть в логах или в админке (при включённом логировании).
⌨️ Управляющие команды
Команда	Описание
python manage.py check_overdue_tasks	Находит просроченные задачи и создаёт уведомления для исполнителей.
python manage.py clean_notifications --days 30	Удаляет прочитанные уведомления старше N дней.
python manage.py cancel_expired_payments	Отменяет в ЮKassa платежи с истёкшим сроком действия ссылки (в учебном режиме просто меняет статус).
python manage.py update_contract_statuses	Обновляет статусы контрактов (активный/завершённый) по датам.
python manage.py populate_db	Заполняет базу тестовыми данными (пользователи, клиенты, контракты, задачи).
Пример использования через Docker:

docker-compose exec web python manage.py check_overdue_tasks
🧪 Тестирование
Проект покрыт юнит-тестами для ключевых модулей: модели, API, права доступа, имитация платежей.

Запуск всех тестов
#python manage.py test
Запуск тестов конкретного приложения
python manage.py test clients.tests
python manage.py test contracts.tests
Запуск отдельных тестовых классов или методов
python manage.py test clients.tests.test_api.ClientAPITest.test_manager_sees_only_own_clients
Покрытие тестами
Приложение	Что тестируется
clients	Создание/обновление/удаление клиентов, права доступа (админ, менеджер, наблюдатель), поиск, фильтрация, валидация модели.
contracts	CRUD контрактов, права доступа, сериализаторы (расчёт остатка, процента оплаты), фильтрация, поиск.
contracts.payment_flow	Инициализация платежа (имитация), валидация сумм, обработка вебхука (успех, отмена, ошибки), права на платежи.
Особенности тестирования в учебном режиме
Нет реальных вызовов ЮKassa – все платежи имитируются через генерацию фейковых payment_url и внутренний вебхук.
Тесты вебхука отправляют POST-запросы на эндпоинт yookassa_webhook с тестовыми JSON-данными и проверяют обновление статусов.
Для изоляции тестов используется встроенная тестовая БД (--keepdb опционально).
Непрерывная интеграция (пример для GitHub Actions)
Создайте файл .github/workflows/test.yml:

name: Django CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      env:
        DB_NAME: test_db
        DB_USER: test_user
        DB_PASSWORD: test_pass
        DB_HOST: localhost
        DB_PORT: 5432
      run: |
        python manage.py test --noinput
📝 Логирование
Логи пишутся в два места:

Файл logs/crm.log – ротируемый, содержит INFO и выше.
База данных – модель APILog. В админке Django есть интерфейс для просмотра логов API-запросов, вебхуков и ошибок.
Настройка производится в settings.py (блок LOGGING). Для просмотра логов БД зайдите в админку → Logs → Api logs.

📁 Структура проекта
crm_project_base_model_auth/
├── accounts/            # Пользователи, профили, аутентификация
├── analytics/           # Аналитика, графики
├── clients/             # Клиенты, импорт/экспорт
├── contracts/           # Контракты, платежи, имитация оплаты
├── core/                # Базовые модели, декораторы, контекстные процессоры
├── dashboard/           # Главная панель
├── logs/                # Логирование API и вебхуков
├── notifications/       # Уведомления, настройки
├── tasks/               # Задачи, канбан-доска
├── static/              # CSS, JS, изображения
├── templates/           # HTML-шаблоны
├── utils/               # Вспомогательные модули (экспорт в Excel)
├── docker-compose.yml
├── manage.py
├── requirements.txt
└── .env
🧯 Возможные проблемы и решения
1. Ошибка импорта TimeStampedModel в приложении logs
Решение: Убедитесь, что в logs/models.py добавлен импорт from core.models import TimeStampedModel.
Подробнее: см. коммит, исправляющий middleware и модели.

2. Ошибка подключения к PostgreSQL в Docker
Решение: Проверьте, что контейнер db запущен и переменные в .env совпадают с docker-compose.yml. При первом запуске может потребоваться время на инициализацию.

3. Celery не видит задачи
Решение: Запустите celery -A crm_project_base_model_auth worker --loglevel=info и убедитесь, что REDIS_URL указан верно.

4. Не работают статические файлы
Решение: Выполните python manage.py collectstatic --noinput и проверьте STATIC_ROOT в settings.py. Для Docker убедитесь, что volume смонтирован.

5. Страница оплаты не открывается (учебный режим)
Решение: Проверьте, что в .env не заданы YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY (или заданы пустыми). Код автоматически переключается на имитацию.

6. Тесты не проходят из-за отсутствия модуля logs
Решение: Убедитесь, что приложение logs добавлено в INSTALLED_APPS и выполнены миграции: python manage.py makemigrations logs python manage.py migrate.

📄 Лицензия
Проект создан в учебных целях. Вы можете свободно использовать и модифицировать код для обучения.

Автор: Aleksey Bashkirov
GitHub: [https://github.com/aleksey31111/crm_project_base_model_auth__Diplom_AI/tree/master ]
Дата: апрель 2026

# Тестирование CRM-системы

Этот файл описывает процесс запуска тестов, структуру тестовых наборов и ожидаемые результаты для учебного проекта CRM.

## 📋 Содержание

- [Запуск тестов](#-запуск-тестов)
- [Структура тестов](#-структура-тестов)
- [Что тестируется](#-что-тестируется)
- [Тестовое окружение](#-тестовое-окружение)
- [Примеры запуска](#-примеры-запуска)
- [Непрерывная интеграция](#-непрерывная-интеграция)
- [Устранение неполадок](#-устранение-неполадок)

---

## 🚀 Запуск тестов

### Все тесты (Особенность обнаружения тестов, а не БАГ проекта)
```bash
python manage.py test
```

### Тесты конкретного приложения
```bash
python manage.py test clients.tests

python manage.py test clients.tests --verbosity 2

python manage.py test contracts.tests

python manage.py test contracts.tests --verbosity 2
```

### Отдельный тестовый класс
```bash
python manage.py test clients.tests.test_api.ClientAPITest

python manage.py test clients.tests.test_api.ClientAPITest --verbosity 2
```

### Отдельный тестовый метод
```bash
python manage.py test clients.tests.test_api.ClientAPITest.test_manager_sees_only_own_clients

python manage.py test clients.tests.test_api.ClientAPITest.test_manager_sees_only_own_clients --verbosity 2
```

### С сохранением тестовой базы данных (быстрее при повторных запусках)
```bash
python manage.py test --keepdb
```

### С выводом детализации (уровень подробности 2)
```bash
python manage.py test --verbosity 2
```

---

## 📁 Структура тестов

```
crm_project_base_model_auth/
├── clients/tests/
│   ├── __init__.py
│   ├── test_models.py      # Тесты модели Client
│   └── test_api.py         # Тесты REST API для клиентов
├── contracts/tests/
│   ├── __init__.py
│   ├── test_api.py         # Тесты REST API для контрактов
│   └── test_payment_flow.py # Тесты имитации платежей и вебхука
└── (другие приложения могут добавляться аналогично)
```

---

## ✅ Что тестируется

### clients.tests.test_models
- Создание клиента и проверка полей
- Строковое представление (`__str__`)
- Формирование полного адреса (`full_address`)
- Связь «один ко многим» с контрактами
- Поле `logo` (может быть пустым)

### clients.tests.test_api
- Доступ неаутентифицированных пользователей → 401
- Менеджер видит только своих клиентов
- Администратор видит всех клиентов
- Наблюдатель (`VIEWER`) не видит клиентов
- Создание клиента менеджером
- Редактирование своего клиента
- Запрет редактирования чужого клиента
- Поиск и фильтрация

### contracts.tests.test_api
- Доступ неаутентифицированных → 401
- Менеджер видит только свои контракты
- Администратор видит все контракты
- Наблюдатель не может создавать контракты
- Менеджер может создавать/редактировать свои контракты
- Сериализатор возвращает вычисляемые поля (`remaining_amount`, `payment_percentage`, `payments`)
- Фильтрация по статусу и поиск по номеру

### contracts.tests.test_payment_flow
- Инициализация платежа (имитация):
  - Неавторизованный → 401
  - Наблюдатель → 404 (нет доступа к контракту)
  - Менеджер → 201, создаётся фейковый платёж с `confirmation_url`
  - Сумма по умолчанию = остаток по контракту
  - Ошибки: сумма > остатка, контракт уже оплачен, отрицательная сумма
  - Запрет инициировать платеж для чужого контракта → 404
- Вебхук (имитация получения уведомления):
  - Успешный платёж → обновление `Payment` и `Contract`
  - Полная оплата → статус `paid`
  - Отмена платежа → статус `canceled`
  - Неизвестный `payment_id` → 404
  - Неподдерживаемое событие → 400
  - Невалидный JSON → 400
  - Неверный метод HTTP → 405
- Права доступа к платежам:
  - Админ видит все платежи
  - Менеджер не видит чужие платежи
  - Менеджер видит платежи по своим контрактам

---

## 🧪 Тестовое окружение

По умолчанию Django создаёт временную базу данных (`test_<имя_боевой_БД>`). Для PostgreSQL или SQLite настройки берутся из `DATABASES` (кроме `NAME` – добавляется префикс `test_`). Можно явно задать тестовую БД в `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'crm_db',
        'TEST': {
            'NAME': 'test_crm_db',
        },
        ...
    }
}
```

**Важно**: Все тесты работают **без реальных внешних вызовов** (ЮKassa замокана или заменена имитацией). Для запуска тестов не требуется регистрация в платёжной системе.

---

## 📝 Примеры запуска

```bash
# Активация виртуального окружения
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Установка зависимостей (если не сделано)
pip install -r requirements.txt

# Запуск всех тестов с покрытием (при установленном coverage)
coverage run manage.py test
coverage report -m

# Только тесты API клиентов
python manage.py test clients.tests.test_api

# Только тесты платежей
python manage.py test contracts.tests.test_payment_flow

python manage.py test contracts.tests.test_payment_flow --verbosity 2''

# Запуск с параллельным выполнением (требуется Python 3.12+)
python manage.py test --parallel
```

---

## 🔁 Непрерывная интеграция (GitHub Actions)

Пример конфигурации `.github/workflows/test.yml`:

```yaml
name: Django Tests

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
```

---

## ⚠️ Устранение неполадок

| Проблема | Решение |
|----------|---------|
| `ModuleNotFoundError: No module named 'logs'` | Добавьте `'logs'` в `INSTALLED_APPS` и выполните `makemigrations logs && migrate` |
| `ImportError: cannot import name 'TimeStampedModel'` | Убедитесь, что `core.models` экспортирует этот класс, и импорт в `logs/models.py` корректен |
| Тесты падают из-за отсутствия БД PostgreSQL | Установите PostgreSQL локально или используйте SQLite (временно измените `ENGINE` в `settings.py`) |
| Ошибка `django.db.utils.OperationalError: FATAL: database "test_crm_db" does not exist` | Убедитесь, что тестовый пользователь имеет права на создание БД. Для PostgreSQL: `ALTER USER test_user CREATEDB;` |
| Тесты платежей падают с `KeyError: 'YOOKASSA_SHOP_ID'` | Добавьте пустые переменные в `.env` или установите `os.environ` в `setUpTestData` |

---

## 📊 Ожидаемые результаты

При успешном прохождении всех тестов вы увидите примерно следующее:

```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.............................
----------------------------------------------------------------------
Ran 35 tests in 2.345s

OK
Destroying test database for alias 'default'...
```

Количество тестов может варьироваться (ориентировочно 30–40 тестов).

---

## 🔗 Дополнительно

- Для измерения покрытия кода тестами используйте `coverage.py`:
  ```bash
  coverage run manage.py test
  coverage html
  open htmlcov/index.html
  ```
- Для отладки тестов добавьте `breakpoint()` внутри теста или запустите:
  ```bash
  python -m pdb manage.py test clients.tests.test_api
  ```

---

**Автор**: Aleksey Bashkirov  
**GitHub**: [https://github.com/aleksey31111]

**Дата составления**: апрель 2026  
**Актуально для версии**: 1.0.0
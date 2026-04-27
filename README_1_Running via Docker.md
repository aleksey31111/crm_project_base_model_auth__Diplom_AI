# CRM система управления клиентами, контрактами и задачами

## Запуск через Docker

1. Склонируйте репозиторий
2. Скопируйте `.env.example` в `.env` и заполните переменные
3. Выполните:


   Стандартная команда для запуска всех сервисов проекта в фоновом режиме с принудительной пересборкой образов.
```bash
docker-compose up -d --build
```

   Примененение миграций для проекта в Docker

```bash
docker-compose exec web python manage.py migrate
```
   Выполняет команду в уже запущенном контейнере сервиса web, и запускает сбор статики, 
флаг --noinput подавляет запрос подтверждения (полезно в автоматизированных скриптах):
```bash
docker-compose exec web python manage.py collectstatic --noinput
```
   Выполняет команду в уже запущенном контейнере сервиса web, и создает СуперПользователя:
```bash 
docker-compose exec web python manage.py createsuperuser
```
   3.1 Запустите контейнеры:
```bash
docker-compose up -d
```
   3.2 Выполните миграции (если ещё не делали):
```bash
docker-compose exec web python manage.py migrate
```
   3.3 Собираем статические данные
```bash
docker-compose exec web python manage.py collectstatic --noinput
```
   3.4 Заполните базу тестовыми данными:
```bash
docker-compose exec web python manage.py populate_db_docker
```
   3.5 Создайте суперпользователя (администратор уже создан скриптом, пароль admin123). 
Если нужно, создайте дополнительного:
```bash
docker-compose exec web python manage.py createsuperuser
```   
   3.6 Остановка Docker
```bash
docker-compose down
```   

## 📄 Лицензия

Проект создан в учебных целях. Вы можете свободно использовать и модифицировать код для обучения.

---

**Автор**: Aleksey Bashkirov  
**GitHub**: [https://github.com/aleksey31111/crm_project_base_model_auth__Diplom_AI/tree/master ]  
**Дата**: апрель 2026
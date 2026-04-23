# CRM система управления клиентами, контрактами и задачами

## Запуск через Docker

1. Склонируйте репозиторий
2. Скопируйте `.env.example` в `.env` и заполните переменные
3. Выполните:
```bash
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose exec web python manage.py createsuperuser
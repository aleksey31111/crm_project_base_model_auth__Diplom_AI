# core/context_processor.py

"""
Контекстные процессоры для добавления данных во все шаблоны.
"""

from django.conf import settings


def site_settings(request):
    """
    Добавление настроек сайта в контекст шаблона.
    """
    return {
        'SITE_NAME': 'CRM System',
        'SITE_VERSION': '1.0.0',
        'DEBUG': settings.DEBUG,
        'COPYRIGHT_YEAR': 2024,
    }


def user_notifications(request):
    """
    Добавление уведомлений пользователя в контекст.
    """
    if request.user.is_authenticated:
        # Здесь можно добавить запрос к модели уведомлений
        notifications_count = 0
        return {
            'notifications_count': notifications_count,
        }
    return {}


def breadcrumbs(request):
    """
    Добавление хлебных крошек в контекст.
    """
    breadcrumbs = []
    path = request.path.split('/')

    if request.user.is_authenticated:
        breadcrumbs.append({'title': 'Главная', 'url': '/'})

        if 'clients' in path:
            breadcrumbs.append({'title': 'Клиенты', 'url': '/clients/'})
        elif 'contracts' in path:
            breadcrumbs.append({'title': 'Контракты', 'url': '/contracts/'})
        elif 'tasks' in path:
            breadcrumbs.append({'title': 'Задачи', 'url': '/tasks/'})

    return {'breadcrumbs': breadcrumbs}

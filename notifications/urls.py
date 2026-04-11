# notifications/urls.py

"""
URL-маршруты для приложения notifications.
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Список уведомлений
    path('', views.NotificationListView.as_view(), name='notification_list'),

    # Детальная информация об уведомлении
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),

    # Отметить как прочитанное
    path('<int:pk>/read/', views.mark_as_read, name='mark_as_read'),

    # Отметить все как прочитанные
    path('read-all/', views.mark_all_as_read, name='mark_all_as_read'),

    # Удалить уведомление
    path('<int:pk>/delete/', views.delete_notification, name='delete_notification'),

    # Настройки уведомлений
    path('settings/', views.notification_settings, name='notification_settings'),

    # API для получения новых уведомлений
    path('api/unread-count/', views.unread_count_api, name='unread_count_api'),
]

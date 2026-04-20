# clients/urls.py

"""
URL-маршруты для приложения clients.
"""

from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Список клиентов
    path('', views.ClientListView.as_view(), name='client_list'),

    # Детальная информация о клиенте
    path('<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),

    # Создание нового клиента
    path('create/', views.ClientCreateView.as_view(), name='client_create'),

    # Редактирование клиента
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),

    # Удаление клиента
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),

    # Экспорт клиентов
    path('export/', views.export_clients, name='client_export'),

    # Импорт клиентов
    path('import/', views.import_clients, name='client_import'),
    path('export/excel/', views.export_clients_excel, name='client_export_excel'),
    path('import/csv/', views.import_clients_ajax, name='client_import_csv')
]

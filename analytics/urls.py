# analytics/urls.py

"""
URL-маршруты для приложения analytics.
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Главная страница аналитики
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),

    # Отчет по продажам
    path('sales/', views.SalesReportView.as_view(), name='sales_report'),

    # Отчет по клиентам
    path('clients/', views.ClientsReportView.as_view(), name='clients_report'),

    # Отчет по задачам
    path('tasks/', views.TasksReportView.as_view(), name='tasks_report'),

    # Отчет по контрактам
    path('contracts/', views.ContractsReportView.as_view(), name='contracts_report'),

    # Экспорт отчета в Excel
    path('export/<str:report_type>/', views.export_report, name='export_report'),

    # API для графиков
    path('api/chart-data/', views.chart_data_api, name='chart_data'),
]

# analytics/views.py

"""
Представления для приложения analytics.
"""

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from clients.models import Client
from contracts.models import Contract
from tasks.models import Task


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """
    Панель аналитики.
    """
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Статистика по клиентам
        context['total_clients'] = Client.objects.count()
        context['active_clients'] = Client.objects.filter(status='active').count()
        context['new_clients_month'] = Client.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()

        # Статистика по контрактам
        context['total_contracts'] = Contract.objects.count()
        context['active_contracts'] = Contract.objects.filter(status='active').count()
        total_amount = Contract.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_amount'] = total_amount

        # Статистика по задачам
        context['total_tasks'] = Task.objects.count()
        context['completed_tasks'] = Task.objects.filter(status='completed').count()
        context['overdue_tasks'] = Task.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'active']
        ).count()

        return context


class SalesReportView(LoginRequiredMixin, TemplateView):
    """
    Отчет по продажам.
    """
    template_name = 'analytics/sales_report.html'


class ClientsReportView(LoginRequiredMixin, TemplateView):
    """
    Отчет по клиентам.
    """
    template_name = 'analytics/clients_report.html'


class TasksReportView(LoginRequiredMixin, TemplateView):
    """
    Отчет по задачам.
    """
    template_name = 'analytics/tasks_report.html'


class ContractsReportView(LoginRequiredMixin, TemplateView):
    """
    Отчет по контрактам.
    """
    template_name = 'analytics/contracts_report.html'


def export_report(request, report_type):
    """
    Экспорт отчета.
    """
    return render(request, 'analytics/export_report.html')


def chart_data_api(request):
    """
    API для получения данных графиков.
    """
    import json
    from django.http import JsonResponse

    data = {
        'labels': ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн'],
        'datasets': [{
            'label': 'Клиенты',
            'data': [65, 59, 80, 81, 56, 55],
        }]
    }
    return JsonResponse(data)

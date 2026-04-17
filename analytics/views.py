# analytics/views.py
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse, JsonResponse
import csv
import json

from clients.models import Client
from contracts.models import Contract
from tasks.models import Task


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """Главная панель аналитики"""
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Клиенты
        context['total_clients'] = Client.objects.count()
        context['active_clients'] = Client.objects.filter(status='active').count()
        context['new_clients_month'] = Client.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()

        # Контракты
        context['total_contracts'] = Contract.objects.count()
        context['active_contracts'] = Contract.objects.filter(status='active').count()
        total_amount = Contract.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_amount'] = total_amount

        # Задачи
        context['total_tasks'] = Task.objects.count()
        context['completed_tasks'] = Task.objects.filter(status='completed').count()
        # Учитываем статусы задач (в модели Task.Status: 'new','in_progress','completed','cancelled')
        context['overdue_tasks'] = Task.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['new', 'in_progress']
        ).count()

        # Данные для графика выручки по месяцам (последние 6 месяцев)
        months = []
        revenues = []
        for i in range(5, -1, -1):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_start = month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            months.append(month_start.strftime('%b %Y'))
            total = Contract.objects.filter(
                signed_date__range=(month_start, month_end)
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            revenues.append(float(total))
        context['months'] = months
        context['revenues'] = revenues

        # Статусы задач для круговой диаграммы
        task_statuses = Task.objects.values('status').annotate(count=Count('id'))
        status_labels = []
        status_data = []
        for item in task_statuses:
            status_labels.append(dict(Task.Status.choices).get(item['status'], item['status']))
            status_data.append(item['count'])
        context['status_labels'] = status_labels
        context['status_data'] = status_data

        return context


class SalesReportView(LoginRequiredMixin, TemplateView):
    """Отчёт по продажам (контрактам)"""
    template_name = 'analytics/sales_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Общая сумма всех контрактов
        total_sales = Contract.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_sales'] = total_sales

        # Сумма по типам контрактов
        sales_by_type = Contract.objects.values('type').annotate(total=Sum('amount'))
        context['sales_by_type'] = sales_by_type

        # Сумма по менеджерам
        sales_by_manager = Contract.objects.values('manager__username', 'manager__first_name', 'manager__last_name')\
            .annotate(total=Sum('amount')).order_by('-total')
        context['sales_by_manager'] = sales_by_manager

        # Количество контрактов по статусам
        contracts_by_status = Contract.objects.values('status').annotate(count=Count('id'))
        context['contracts_by_status'] = contracts_by_status

        # Сумма оплаченных и неоплаченных
        paid_amount = Contract.objects.filter(payment_status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
        unpaid_amount = Contract.objects.exclude(payment_status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
        context['paid_amount'] = paid_amount
        context['unpaid_amount'] = unpaid_amount

        return context


class ClientsReportView(LoginRequiredMixin, TemplateView):
    """Отчёт по клиентам"""
    template_name = 'analytics/clients_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Общее количество клиентов
        context['total_clients'] = Client.objects.count()

        # По типам клиентов
        clients_by_type = Client.objects.values('type').annotate(count=Count('id'))
        context['clients_by_type'] = clients_by_type

        # По статусам
        clients_by_status = Client.objects.values('status').annotate(count=Count('id'))
        context['clients_by_status'] = clients_by_status

        # По менеджерам
        clients_by_manager = Client.objects.values('manager__username', 'manager__first_name', 'manager__last_name')\
            .annotate(count=Count('id')).order_by('-count')
        context['clients_by_manager'] = clients_by_manager

        # Клиенты с наибольшим количеством контрактов
        top_clients = Client.objects.annotate(contracts_count=Count('contracts')).order_by('-contracts_count')[:10]
        context['top_clients'] = top_clients

        return context


class TasksReportView(LoginRequiredMixin, TemplateView):
    """Отчёт по задачам"""
    template_name = 'analytics/tasks_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Общее количество задач
        context['total_tasks'] = Task.objects.count()
        context['completed_tasks'] = Task.objects.filter(status='completed').count()
        context['overdue_tasks'] = Task.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['new', 'in_progress']
        ).count()

        # По статусам
        tasks_by_status = Task.objects.values('status').annotate(count=Count('id'))
        context['tasks_by_status'] = tasks_by_status

        # По приоритетам
        tasks_by_priority = Task.objects.values('priority').annotate(count=Count('id'))
        context['tasks_by_priority'] = tasks_by_priority

        # По исполнителям
        tasks_by_assignee = Task.objects.values('assigned_to__username', 'assigned_to__first_name', 'assigned_to__last_name')\
            .annotate(count=Count('id')).order_by('-count')
        context['tasks_by_assignee'] = tasks_by_assignee

        # Просроченные задачи (список)
        overdue_tasks_list = Task.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['new', 'in_progress']
        ).order_by('due_date')[:20]
        context['overdue_tasks_list'] = overdue_tasks_list

        return context


class ContractsReportView(LoginRequiredMixin, TemplateView):
    """Отчёт по контрактам (расширенный)"""
    template_name = 'analytics/contracts_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Общая статистика
        context['total_contracts'] = Contract.objects.count()
        context['active_contracts'] = Contract.objects.filter(status='active').count()
        context['expired_contracts'] = Contract.objects.filter(end_date__lt=timezone.now()).count()
        context['total_amount'] = Contract.objects.aggregate(Sum('amount'))['amount__sum'] or 0

        # По типам
        contracts_by_type = Contract.objects.values('type').annotate(count=Count('id'), total=Sum('amount'))
        context['contracts_by_type'] = contracts_by_type

        # По статусам оплаты
        contracts_by_payment = Contract.objects.values('payment_status').annotate(count=Count('id'), total=Sum('amount'))
        context['contracts_by_payment'] = contracts_by_payment

        # Контракты с истекающим сроком (следующие 30 дней)
        soon_expiring = Contract.objects.filter(
            end_date__gte=timezone.now(),
            end_date__lte=timezone.now() + timedelta(days=30),
            status='active'
        ).order_by('end_date')[:20]
        context['soon_expiring'] = soon_expiring

        return context


def export_report(request, report_type):
    """Экспорт отчёта в CSV или Excel (заглушка – CSV)"""
    # Определяем модель и данные в зависимости от report_type
    if report_type == 'sales':
        data = Contract.objects.values('number', 'title', 'client__full_name', 'amount', 'paid_amount', 'status', 'created_at')
        filename = 'sales_report.csv'
        headers = ['Номер', 'Название', 'Клиент', 'Сумма', 'Оплачено', 'Статус', 'Дата создания']
    elif report_type == 'clients':
        data = Client.objects.values('full_name', 'type', 'status', 'email', 'phone', 'created_at')
        filename = 'clients_report.csv'
        headers = ['Наименование', 'Тип', 'Статус', 'Email', 'Телефон', 'Дата создания']
    elif report_type == 'tasks':
        data = Task.objects.values('title', 'status', 'priority', 'assigned_to__username', 'due_date', 'created_at')
        filename = 'tasks_report.csv'
        headers = ['Название', 'Статус', 'Приоритет', 'Исполнитель', 'Срок', 'Дата создания']
    elif report_type == 'contracts':
        data = Contract.objects.values('number', 'title', 'client__full_name', 'amount', 'payment_status', 'status', 'start_date', 'end_date')
        filename = 'contracts_report.csv'
        headers = ['Номер', 'Название', 'Клиент', 'Сумма', 'Статус оплаты', 'Статус', 'Дата начала', 'Дата окончания']
    else:
        return HttpResponse('Неверный тип отчёта', status=400)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in data:
        writer.writerow([str(v) for v in row.values()])
    return response


def chart_data_api(request):
    """API для графиков: выручка по месяцам, задачи по статусам и т.д."""
    # Параметры: chart_type (revenue, tasks_status)
    chart_type = request.GET.get('type', 'revenue')
    if chart_type == 'revenue':
        # Выручка по месяцам за последние 12 месяцев
        months = []
        revenues = []
        for i in range(11, -1, -1):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_start = month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            months.append(month_start.strftime('%b %Y'))
            total = Contract.objects.filter(
                signed_date__range=(month_start, month_end)
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            revenues.append(float(total))
        return JsonResponse({'labels': months, 'data': revenues})
    elif chart_type == 'tasks_status':
        statuses = Task.objects.values('status').annotate(count=Count('id'))
        labels = [dict(Task.Status.choices).get(s['status'], s['status']) for s in statuses]
        data = [s['count'] for s in statuses]
        return JsonResponse({'labels': labels, 'data': data})
    else:
        return JsonResponse({'error': 'Unknown chart type'}, status=400)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from contracts.models import Contract
from tasks.models import Task
from clients.models import Client

@login_required
def index(request):
    # Данные для графика выручки по месяцам (последние 6 месяцев)
    today = timezone.now().date()
    months = []
    revenues = []
    for i in range(5, -1, -1):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        months.append(month_start.strftime('%b %Y'))
        # Сумма контрактов, созданных в этом месяце
        total = Contract.objects.filter(
            created_at__year=month_start.year,
            created_at__month=month_start.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        revenues.append(float(total))

    # Статусы задач для круговой диаграммы
    task_statuses = Task.objects.values('status').annotate(count=Count('id'))
    status_labels = []
    status_data = []
    for item in task_statuses:
        status_labels.append(dict(Task.Status.choices).get(item['status'], item['status']))
        status_data.append(item['count'])

    # Статистика для карточек
    total_clients = Client.objects.count()
    active_contracts = Contract.objects.filter(status='active').count()
    total_revenue = Contract.objects.filter(status='active').aggregate(Sum('amount'))['amount__sum'] or 0
    overdue_tasks = Task.objects.filter(
        due_date__lt=timezone.now(),
        status__in=['new', 'in_progress']
    ).count()

    context = {
        'months': months,
        'revenues': revenues,
        'status_labels': status_labels,
        'status_data': status_data,
        'total_clients': total_clients,
        'active_contracts': active_contracts,
        'total_revenue': total_revenue,
        'overdue_tasks': overdue_tasks,
    }
    return render(request, 'dashboard/index.html', context)

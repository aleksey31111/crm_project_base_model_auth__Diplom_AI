# dashboard/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from clients.models import Client
from tasks.models import Task
from contracts.models import Contract

total_contracts = Contract.objects.count()
active_contracts = Contract.objects.filter(status='active').count()
contracts_amount_sum = Contract.objects.aggregate(Sum('amount'))['amount__sum'] or 0

@login_required
def index(request):
    """Главная страница дашборда"""

    # Статистика для текущего пользователя
    context = {
        # Общая статистика
        'total_clients': Client.objects.count(),
        'total_contracts': Contract.objects.count(),
        'total_tasks': Task.objects.count(),
        'my_tasks': Task.objects.filter(assigned_to=request.user).count(),

        # Статистика за сегодня
        'today_tasks': Task.objects.filter(
            due_date__date=timezone.now().date()
        ).count(),

        # Просроченные задачи
        'overdue_tasks': Task.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'active']
        ).count(),

        # Последние записи
        'recent_clients': Client.objects.order_by('-created_at')[:5],
        'recent_tasks': Task.objects.filter(
            assigned_to=request.user
        ).order_by('-created_at')[:5],
        'recent_contracts': Contract.objects.order_by('-created_at')[:5],
    }

    return render(request, 'dashboard/index.html', context)


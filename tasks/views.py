# tasks/views.py

"""
Представления для приложения tasks.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone

from .forms import TaskForm
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Task, TaskComment




class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        """Возвращает queryset для списка задач (с учётом фильтров)"""
        queryset = super().get_queryset().select_related('assigned_to', 'client', 'contract')
        user = self.request.user

        # Ограничение по роли: если не админ/менеджер, только свои задачи
        if not (user.role in ['ADMIN', 'MANAGER'] or user.is_superuser):
            queryset = queryset.filter(assigned_to=user)

        # Фильтры
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(title__icontains=search)

        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        priority = self.request.GET.get('priority', '')
        if priority:
            queryset = queryset.filter(priority=priority)

        if self.request.GET.get('assigned_to') == 'me':
            queryset = queryset.filter(assigned_to=user)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ---- Базовый queryset для статистики (без фильтра по статусу) ----
        base_qs = super().get_queryset().select_related('assigned_to', 'client', 'contract')
        user = self.request.user
        if not (user.role in ['ADMIN', 'MANAGER'] or user.is_superuser):
            base_qs = base_qs.filter(assigned_to=user)

        # Применяем к статистике ТОЛЬКО поиск, приоритет и назначение (но не статус!)
        search = self.request.GET.get('search', '')
        if search:
            base_qs = base_qs.filter(title__icontains=search)

        priority = self.request.GET.get('priority', '')
        if priority:
            base_qs = base_qs.filter(priority=priority)

        if self.request.GET.get('assigned_to') == 'me':
            base_qs = base_qs.filter(assigned_to=user)

        now = timezone.now()
        context['total_tasks'] = base_qs.count()
        context['in_progress_tasks'] = base_qs.filter(status='in_progress').count()
        context['completed_tasks'] = base_qs.filter(status='completed').count()
        context['overdue_tasks'] = base_qs.filter(
            due_date__lt=now,
            status__in=['new', 'in_progress']
        ).count()

        # Передаём текущие значения фильтров в шаблон
        context['search_query'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        context['assigned_to_me'] = self.request.GET.get('assigned_to') == 'me'
        context['status_choices'] = Task.Status.choices
        context['priority_choices'] = Task.Priority.choices

        return context

class MyTaskListView(LoginRequiredMixin, ListView):
    """
    Список задач текущего пользователя.
    """
    model = Task
    template_name = 'tasks/my_tasks.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        return Task.objects.filter(
            assigned_to=self.request.user
        ).select_related('client', 'created_by').order_by('due_date')


class TaskDetailView(LoginRequiredMixin, DetailView):
    """
    Детальная информация о задаче.
    """
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all().order_by('-created_at')
        return context


# class TaskCreateView(LoginRequiredMixin, CreateView):
#     """
#     Создание новой задачи.
#     """
#     model = Task
#     template_name = 'tasks/task_form.html'
#     fields = [
#         'title', 'description', 'client', 'contract',
#         'assigned_to', 'priority', 'due_date',
#         'estimated_hours', 'notes'
#     ]
#     success_url = reverse_lazy('tasks:task_list')
#
#     def form_valid(self, form):
#         form.instance.created_by = self.request.user
#         messages.success(self.request, 'Задача успешно создана.')
#         return super().form_valid(form)

class TaskCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def test_func(self):
        """Разрешить создание задач только администраторам и менеджерам"""
        user = self.request.user
        return user.is_authenticated and (user.role in ['ADMIN', 'MANAGER'] or user.is_superuser)

    def handle_no_permission(self):
        # Если нет прав, можно выдать сообщение и перенаправить на список задач
        from django.contrib import messages
        messages.error(self.request, 'У вас нет прав на создание задач.')
        return redirect('tasks:task_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Задача успешно обновлена.')
        return super().form_valid(form)


class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Удаление задачи. Доступно только администраторам и менеджерам.
    """
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.role in ['ADMIN', 'MANAGER'] or user.is_superuser)

    def handle_no_permission(self):
        messages.error(self.request, 'У вас нет прав на удаление задач.')
        return redirect('tasks:task_list')


def change_task_status(request, pk):
    """
    Изменение статуса задачи.
    """
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Task.Status.choices):
            task.status = new_status
            if new_status == 'completed':
                task.completed_at = timezone.now()
            task.save()
            messages.success(request, f'Статус задачи изменен на {task.get_status_display()}')

    return redirect('tasks:task_detail', pk=pk)


def add_task_comment(request, pk):
    """
    Добавление комментария к задаче.
    """
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        if comment_text:
            TaskComment.objects.create(
                task=task,
                comment=comment_text,
                created_by=request.user
            )
            messages.success(request, 'Комментарий добавлен.')

    return redirect('tasks:task_detail', pk=pk)

class OverdueTasksView(LoginRequiredMixin, ListView):
    """Просроченные задачи текущего пользователя"""
    model = Task
    template_name = 'tasks/task_list.html'   # переиспользуем шаблон списка задач
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        return Task.objects.filter(
            assigned_to=self.request.user,
            # due_date__lt=date.today(),
            due_date__lt=timezone.now().date(),
            status__in=['new', 'in_progress']
        ).order_by('due_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Просроченные задачи'
        return context



@login_required
def kanban_board(request):
    """Отображение Kanban-доски"""
    if request.user.role in ['ADMIN', 'MANAGER'] or request.user.is_superuser:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(assigned_to=request.user)

    statuses = ['new', 'in_progress', 'completed', 'cancelled']
    status_display = dict(Task.Status.choices)
    columns = {}
    for status in statuses:
        columns[status] = {
            'title': status_display[status],
            'tasks': tasks.filter(status=status).order_by('due_date')
        }
    return render(request, 'tasks/kanban_board.html', {'columns': columns})


@require_POST
@login_required
def update_task_status(request, task_id):
    """API для обновления статуса задачи (drag-and-drop)"""
    import json
    task = get_object_or_404(Task, id=task_id)
    # Проверка прав
    if task.assigned_to != request.user and request.user.role not in ['ADMIN', 'MANAGER']:
        return JsonResponse({'success': False, 'error': 'Нет прав'}, status=403)

    data = json.loads(request.body)
    new_status = data.get('status')
    if new_status not in dict(Task.Status.choices):
        return JsonResponse({'success': False, 'error': 'Неверный статус'}, status=400)

    task.status = new_status
    if new_status == 'completed' and not task.completed_at:
        from django.utils import timezone
        task.completed_at = timezone.now()
    task.save()
    return JsonResponse({'success': True})



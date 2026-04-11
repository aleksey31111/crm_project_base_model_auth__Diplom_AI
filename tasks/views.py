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
from .models import Task, TaskComment
from .forms import TaskForm


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Если пользователь не администратор и не менеджер, показываем только его задачи
        if not (user.role in ['ADMIN', 'MANAGER'] or user.is_superuser):
            queryset = queryset.filter(assigned_to=user)

        queryset = super().get_queryset().select_related('assigned_to', 'client', 'contract')

        # Поиск
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(title__icontains=search)

        # Статус
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        # Приоритет
        priority = self.request.GET.get('priority', '')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Назначено
        assigned_to = self.request.GET.get('assigned_to', '')
        if assigned_to == 'me':
            queryset = queryset.filter(assigned_to=self.request.user)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем отфильтрованный queryset для статистики
        qs = self.get_queryset()

        context['total_tasks'] = qs.count()
        context['in_progress_tasks'] = qs.filter(status='in_progress').count()
        context['completed_tasks'] = qs.filter(status='completed').count()

        now = timezone.now()
        context['overdue_tasks'] = qs.filter(
            due_date__lt=now,
            status__in=['new', 'in_progress']
        ).count()

        # Передаём текущие значения фильтров в шаблон
        context['search_query'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        context['assigned_to_me'] = self.request.GET.get('assigned_to') == 'me'

        # Списки для выпадающих меню
        context['status_choices'] = Task.Status.choices
        context['priority_choices'] = Task.Priority.choices

        return context

    # def get_queryset(self):
    #     # Здесь может быть ваша фильтрация (поиск, статус, приоритет, назначенный пользователь)
    #     queryset = super().get_queryset()
    #     # Пример: если нужно показывать задачи только текущего пользователя
    #     # if not self.request.user.is_superuser:
    #     #     queryset = queryset.filter(assigned_to=self.request.user)
    #     return queryset
    #
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #
    #     # Получаем все задачи с учётом тех же фильтров, что и в списке
    #     tasks_qs = self.get_queryset()
    #
    #     # Подсчитываем статистику
    #     context['total_tasks'] = tasks_qs.count()
    #     context['in_progress_tasks'] = tasks_qs.filter(status='in_progress').count()
    #     context['completed_tasks'] = tasks_qs.filter(status='completed').count()
    #
    #     # Просроченные задачи: дата выполнения меньше текущей и статус не 'completed'
    #     now = timezone.now()
    #     context['overdue_tasks'] = tasks_qs.filter(
    #         due_date__lt=now,
    #         status__in=['new', 'in_progress']
    #     ).count()
    #
    #     return context



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


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление задачи.
    """
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')


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

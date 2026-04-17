# tasks/urls.py

"""
URL-маршруты для приложения tasks.
"""

from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Список задач
    path('', views.TaskListView.as_view(), name='task_list'),

    # Мои задачи
    path('my/', views.MyTaskListView.as_view(), name='my_tasks'),

    # Детальная информация о задаче
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),

    # Создание новой задачи
    path('create/', views.TaskCreateView.as_view(), name='task_create'),

    # Редактирование задачи
    path('<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),

    # Удаление задачи
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),

    # Изменение статуса задачи
    path('<int:pk>/status/', views.change_task_status, name='task_change_status'),

    # Добавление комментария к задаче
    path('<int:pk>/comment/', views.add_task_comment, name='task_add_comment'),
    # path('', views.TaskListView.as_view(), name='task_list'),
    path('overdue/', views.OverdueTasksView.as_view(), name='overdue_tasks'),   # новый маршрут
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('create/', views.TaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),

    path('kanban/', views.kanban_board, name='kanban_board'),
    path('<int:task_id>/update-status/', views.update_task_status, name='update_task_status'),
]

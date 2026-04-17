# clients/views.py

"""
Представления для приложения clients.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
# from core.models import BaseModel
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from .models import Client


class ClientListView(LoginRequiredMixin, ListView):
    """
    Список клиентов.
    """
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Поиск
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(short_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(inn__icontains=search_query)
            )

        # Фильтр по типу
        client_type = self.request.GET.get('type', '')
        if client_type:
            queryset = queryset.filter(type=client_type)

        # Фильтр по статусу
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        # Фильтр по менеджеру
        manager = self.request.GET.get('manager', '')
        if manager:
            queryset = queryset.filter(manager_id=manager)

        return queryset.select_related('manager', 'created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Клиенты'
        context['client_types'] = Client.ClientType.choices
        # context['status_choices'] = Client.Status.choices
        context['status_choices'] = Client._meta.get_field('status').choices
        context['search_query'] = self.request.GET.get('search', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['current_status'] = self.request.GET.get('status', '')
        return context


class ClientDetailView(LoginRequiredMixin, DetailView):
    """
    Детальная информация о клиенте.
    """
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Клиент: {self.object.full_name}'
        context['contracts'] = self.object.contracts.all().order_by('-created_at')[:5]
        context['tasks'] = self.object.tasks.all().order_by('-created_at')[:5]
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    """
    Создание нового клиента.
    """
    model = Client
    template_name = 'clients/client_form.html'
    fields = [
        'type', 'full_name', 'short_name', 'inn', 'kpp', 'ogrn',
        'first_name', 'last_name', 'patronymic', 'birth_date',
        'email', 'phone', 'phone_secondary', 'website', 'address',
        'city', 'country', 'postal_code', 'manager', 'source', 'notes'
    ]
    success_url = reverse_lazy('clients:client_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Клиент успешно создан.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание клиента'
        return context


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """
    Редактирование клиента.
    """
    model = Client
    template_name = 'clients/client_form.html'
    fields = [
        'type', 'full_name', 'short_name', 'inn', 'kpp', 'ogrn',
        'first_name', 'last_name', 'patronymic', 'birth_date',
        'email', 'phone', 'phone_secondary', 'website', 'address',
        'city', 'country', 'postal_code', 'manager', 'source', 'notes',
        'status', 'private_notes'
    ]
    success_url = reverse_lazy('clients:client_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Клиент успешно обновлен.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование: {self.object.full_name}'
        return context


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients:client_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Проверяем наличие связанных контрактов
        if self.object.contracts.exists():
            contract_list = ', '.join([c.number for c in self.object.contracts.all()])
            messages.error(
                request,
                f'Невозможно удалить клиента "{self.object.full_name}", так как у него есть активные контракты: {contract_list}. '
                f'Сначала удалите или переназначьте контракты.'
            )
            return redirect('clients:client_detail', pk=self.object.pk)
        # Если контрактов нет – удаляем
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'Клиент "{self.object.full_name}" успешно удалён.')
        return redirect(success_url)

def export_clients(request):
    """
    Экспорт клиентов в Excel/CSV.
    """
    # Здесь будет логика экспорта
    messages.info(request, 'Функция экспорта в разработке.')
    return redirect('clients:client_list')


def import_clients(request):
    """
    Импорт клиентов из Excel/CSV.
    """
    # Здесь будет логика импорта
    messages.info(request, 'Функция импорта в разработке.')
    return redirect('clients:client_list')

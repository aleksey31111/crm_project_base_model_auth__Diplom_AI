# contracts/views.py

"""
Представления для приложения contracts.
"""

from datetime import timedelta, date
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum
from django.db.models import Q
from .models import Contract, Payment
from .forms import PaymentForm
import csv
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

class ContractExportView(LoginRequiredMixin, View):
    """Экспорт контрактов в CSV"""
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contracts.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Номер', 'Название', 'Клиент', 'Тип', 'Сумма', 'Оплачено',
            'Статус оплаты', 'Статус', 'Дата начала', 'Дата окончания', 'Менеджер'
        ])

        contracts = Contract.objects.select_related('client', 'manager').all()
        for c in contracts:
            writer.writerow([
                c.id, c.number, c.title, c.client.full_name if c.client else '',
                c.get_type_display(), c.amount, c.paid_amount,
                c.get_payment_status_display(), c.get_status_display(),
                c.start_date, c.end_date, str(c.manager) if c.manager else ''
            ])

        return response


class ContractListView(LoginRequiredMixin, ListView):
    """
    Список контрактов.
    """
    model = Contract
    template_name = 'contracts/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(number__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(client__full_name__icontains=search_query)
            )

        return queryset.select_related('client', 'manager')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Контракты'
        context['search_query'] = self.request.GET.get('search', '')
        return context

    def export_contracts_csv(request):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contracts.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ['ID', 'Номер', 'Название', 'Клиент', 'Сумма', 'Оплачено', 'Статус', 'Дата начала', 'Дата окончания'])

        contracts = Contract.objects.all()
        for c in contracts:
            writer.writerow(
                [c.id, c.number, c.title, c.client.full_name, c.amount, c.paid_amount, c.get_status_display(),
                 c.start_date, c.end_date])

        return response


class ContractDetailView(LoginRequiredMixin, DetailView):
    """
    Детальная информация о контракте.
    """
    model = Contract
    template_name = 'contracts/contract_detail.html'
    context_object_name = 'contract'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Контракт: {self.object.number}'
        return context


class ContractCreateView(LoginRequiredMixin, CreateView):
    """
    Создание нового контракта.
    """
    model = Contract
    template_name = 'contracts/contract_form.html'
    fields = [
        'client', 'number', 'type', 'title', 'description',
        'start_date', 'end_date', 'signed_date', 'amount',
        'manager', 'document', 'notes'
    ]
    success_url = reverse_lazy('contracts:contract_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Контракт успешно создан.')
        return super().form_valid(form)


class ContractUpdateView(LoginRequiredMixin, UpdateView):
    """
    Редактирование контракта.
    """
    model = Contract
    template_name = 'contracts/contract_form.html'
    fields = [
        'title', 'description', 'end_date', 'signed_date',
        'amount', 'paid_amount', 'status', 'document', 'notes'
    ]
    success_url = reverse_lazy('contracts:contract_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Контракт успешно обновлен.')
        return super().form_valid(form)


class ContractDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление контракта.
    """
    model = Contract
    template_name = 'contracts/contract_confirm_delete.html'
    success_url = reverse_lazy('contracts:contract_list')


def renew_contract(request, pk):
    """
    Продление контракта.
    """
    contract = get_object_or_404(Contract, pk=pk)
    messages.success(request, f'Контракт {contract.number} продлен.')
    return redirect('contracts:contract_detail', pk=pk)


def contract_payments(request, pk):
    """
    Просмотр и управление оплатами по контракту.
    """
    contract = get_object_or_404(Contract, pk=pk)
    return render(request, 'contracts/contract_payments.html', {'contract': contract})


class PaymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'contracts/payment_form.html'
    permission_required = 'contracts.can_manage_payments'

    def dispatch(self, request, *args, **kwargs):
        self.contract = get_object_or_404(Contract, pk=kwargs['contract_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.contract = self.contract
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Платёж успешно добавлен.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('contracts:contract_payments', kwargs={'pk': self.contract.pk})

class PaymentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'contracts/payment_form.html'
    permission_required = 'contracts.can_manage_payments'

    def get_success_url(self):
        return reverse_lazy('contracts:contract_payments', kwargs={'pk': self.object.contract.pk})

class PaymentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Payment
    permission_required = 'contracts.can_manage_payments'
    template_name = 'contracts/payment_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('contracts:contract_payments', kwargs={'pk': self.object.contract.pk})

def renew_contract(request, pk):
    """Продление контракта: создание нового контракта на основе старого с новыми датами"""
    old_contract = get_object_or_404(Contract, pk=pk)
    # Копируем данные
    new_contract = Contract(
        client=old_contract.client,
        number=f"{old_contract.number}/R",  # добавим суффикс
        type=old_contract.type,
        title=f"{old_contract.title} (продление)",
        description=old_contract.description,
        start_date=old_contract.end_date + timedelta(days=1),
        end_date=old_contract.end_date + timedelta(days=365),  # +1 год
        signed_date=date.today(),
        amount=old_contract.amount,
        manager=old_contract.manager,
        status='active',
        created_by=request.user,
    )
    new_contract.save()
    messages.success(request, f'Контракт {old_contract.number} продлён. Новый контракт: {new_contract.number}')
    return redirect('contracts:contract_detail', pk=new_contract.pk)
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
from .forms import PaymentForm
import csv
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from .tasks import send_contract_created_email
from django.shortcuts import render, get_object_or_404
from .models import Contract

######################################################################################################
########### Часть 1. Создание эндпоинта вебхука для уведомлений от ЮKassa ############################
######################################################################################################
# contracts/views.py
import json
import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from yookassa import Configuration
from .models import Contract, Payment
# contracts/views.py
import json
import ipaddress
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from yookassa import Configuration
from .models import Payment, Contract
from .tasks import send_payment_success_notifications   # создадим позже
import logging
from django.shortcuts import render, get_object_or_404
from .models import Contract

def fake_payment_page(request, contract_id):
    from .models import Contract
    contract = get_object_or_404(Contract, id=contract_id)
    return render(request, 'contracts/fake_payment.html', {'contract': contract})


@csrf_exempt
def yookassa_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    # Для учебного проекта проверку IP отключаем
    # if not settings.DEBUG:
    #     if not is_allowed_ip(request):
    #         return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        event_data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    event = event_data.get('event')
    if event not in ['payment.succeeded', 'payment.canceled', 'payment.waiting_for_capture']:
        return JsonResponse({'error': 'Unsupported event'}, status=400)

    payment_id = event_data['object']['id']
    payment_status = event_data['object']['status']

    try:
        payment = Payment.objects.get(yookassa_id=payment_id)
        contract = payment.contract
    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)

    payment.yookassa_status = payment_status
    if payment_status == 'succeeded':
        payment.paid_at = timezone.now()
        payment.save()
        contract.save()
        # При желании можно вызвать задачу уведомления:
        # send_payment_success_notifications.delay(payment.id)
    elif payment_status == 'canceled':
        payment.save()
        contract.payment_url = ''
        contract.yookassa_payment_id = ''
        contract.save(update_fields=['payment_url', 'yookassa_payment_id'])

    return JsonResponse({'status': 'ok'})


logger = logging.getLogger(__name__)


# @csrf_exempt
# def yookassa_webhook(request):
#     """
#     Обработчик уведомлений от ЮKassa.
#     """
#     if request.method != 'POST':
#         return HttpResponse(status=405)
#
#     # Получение тела запроса
#     body = request.body
#     # Проверка подписи (опционально, для безопасности)
#     # Можно проверить IP-адрес отправителя или использовать заголовок `HTTP_CONTENT_SIGNATURE`
#     # Для упрощения пропустим проверку подписи (в реальном проекте обязательно)
#
#     try:
#         event_data = json.loads(body)
#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON'}, status=400)
#
#     # Внутри yookassa_webhook:
#     logger.info(f"Webhook received: {event}, payment_id={payment_id}")
#     if payment_status == 'succeeded':
#         logger.info(f"Payment {payment_id} succeeded, updating contract {contract.id}")
#
#     # Проверяем, что это уведомление о платеже
#     if event_data.get('event') not in ['payment.succeeded', 'payment.canceled', 'payment.waiting_for_capture']:
#         return JsonResponse({'error': 'Unsupported event'}, status=400)
#
#     payment_id = event_data['object']['id']
#     payment_status = event_data['object']['status']
#
#     try:
#         # Находим платёж в нашей системе по yookassa_id
#         payment = Payment.objects.get(yookassa_id=payment_id)
#         contract = payment.contract
#     except Payment.DoesNotExist:
#         return JsonResponse({'error': 'Payment not found'}, status=404)
#
#     # Обновляем статус в нашей модели Payment
#     payment.yookassa_status = payment_status
#     if payment_status == 'succeeded':
#         payment.paid_at = timezone.now()
#         payment.save()
#
#         # Обновляем контракт
#         #contract.paid_amount += payment.amount
#         contract.save()  # save() обновит payment_status
#         # Создаём уведомление менеджеру (опционально)
#         # Notification.objects.create(...)
#     elif payment_status == 'canceled':
#         payment.save()
#         # Можно удалить ссылку на оплату из контракта, если нужно
#
#     return JsonResponse({'status': 'ok'})
########################################################################################################################
########################################################################################################################
########################################################################################################################

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

    # def form_valid(self, form):
    #     form.instance.updated_by = self.request.user
    #     messages.success(self.request, 'Контракт успешно обновлен.')
    #     return super().form_valid(form)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        # Асинхронная отправка email
        send_contract_created_email.delay(self.object.id)
        messages.success(self.request, 'Контракт успешно создан.')
        return response


class ContractDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление контракта.
    """
    model = Contract
    template_name = 'contracts/contract_confirm_delete.html'
    success_url = reverse_lazy('contracts:contract_list')


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

# Разрешённые подсети ЮKassa (актуальны на 2025 год)
YOOKASSA_SUBNETS = [
    '185.71.76.0/27', '185.71.77.0/27', '77.75.153.0/25', '77.75.156.11',
    '77.75.156.35', '77.75.156.131', '77.75.158.0/25', '79.142.16.0/25',
    '79.142.17.0/25', '79.142.18.0/25', '79.142.19.0/25', '79.142.20.0/25',
    '79.142.21.0/25', '79.142.22.0/25', '79.142.23.0/25'
]

# ДОБАВЛЯЕМ: ваша локальная сеть (для тестов, если используете ngrok или проброс)
LOCAL_NETWORKS = [
    '192.168.1.0/24',      # ваша LAN
    '127.0.0.0/8',         # localhost
]

def is_allowed_ip(request):
    """
    Проверяет, что IP-адрес запроса принадлежит либо подсетям ЮKassa,
    либо локальным сетям (только при DEBUG=True).
    """
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    if client_ip:
        client_ip = client_ip.split(',')[0].strip()
        try:
            client_ip_obj = ipaddress.ip_address(client_ip)
            # Всегда разрешаем локальные сети в режиме отладки
            if settings.DEBUG:
                for net in LOCAL_NETWORKS:
                    if client_ip_obj in ipaddress.ip_network(net):
                        return True
            # Проверка на IP ЮKassa
            for subnet in YOOKASSA_SUBNETS:
                if client_ip_obj in ipaddress.ip_network(subnet):
                    return True
        except ValueError:
            pass
    return False

# @csrf_exempt
# def yookassa_webhook(request):
#     if request.method != 'POST':
#         return HttpResponse(status=405)
#
#     # Проверка IP – в боевом режиме только ЮKassa, в DEBUG разрешаем локальные сети
#     if not is_allowed_ip(request):
#         # Логируем попытку несанкционированного доступа
#         print(f"[WARN] Webhook rejected from IP: {request.META.get('REMOTE_ADDR')}")
#         return JsonResponse({'error': 'Forbidden'}, status=403)
#
#     try:
#         event_data = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON'}, status=400)
#
#     event = event_data.get('event')
#     if event not in ['payment.succeeded', 'payment.canceled', 'payment.waiting_for_capture']:
#         return JsonResponse({'error': 'Unsupported event'}, status=400)
#
#     payment_id = event_data['object']['id']
#     payment_status = event_data['object']['status']
#
#     try:
#         payment = Payment.objects.get(yookassa_id=payment_id)
#         contract = payment.contract
#     except Payment.DoesNotExist:
#         return JsonResponse({'error': 'Payment not found'}, status=404)
#
#     # Обновляем статус платежа
#     payment.yookassa_status = payment_status
#     if payment_status == 'succeeded':
#         payment.paid_at = timezone.now()
#         payment.save()
#         contract.save()   # пересчитает paid_amount и payment_status
#         # Асинхронная отправка уведомлений (см. следующий раздел)
#         send_payment_success_notifications.delay(payment.id)
#     elif payment_status == 'canceled':
#         payment.save()
#         # Очищаем ссылку на оплату в контракте
#         contract.payment_url = ''
#         contract.yookassa_payment_id = ''
#         contract.save(update_fields=['payment_url', 'yookassa_payment_id'])
#
#     return JsonResponse({'status': 'ok'})

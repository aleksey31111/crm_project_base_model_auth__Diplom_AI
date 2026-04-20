from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from yookassa import Payment as YooPayment
from .models import Payment, Contract
from django.utils import timezone

@shared_task
def send_contract_created_email(contract_id):
    """Асинхронная отправка email менеджеру при создании контракта"""
    from .models import Contract
    try:
        contract = Contract.objects.select_related('manager', 'client').get(id=contract_id)
        if contract.manager and contract.manager.email:
            subject = f'Новый контракт {contract.number} создан'
            message = f'''
            Здравствуйте, {contract.manager.get_full_name()}!

            Был создан новый контракт:
            Номер: {contract.number}
            Клиент: {contract.client.full_name}
            Сумма: {contract.amount} ₽
            Дата начала: {contract.start_date}
            Дата окончания: {contract.end_date}

            Ссылка: {settings.BASE_URL}/contracts/{contract.id}/
            '''
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contract.manager.email],
                fail_silently=False,
            )
    except Contract.DoesNotExist:
        pass

# contracts/tasks.py

@shared_task
def check_payment_status():
    """
    Периодическая задача для опроса статусов незавершённых платежей в ЮKassa.
    Запускается по расписанию (например, раз в 10 минут).
    """
    # Берём все платежи, которые ещё не завершены (pending или waiting_for_capture)
    pending_payments = Payment.objects.filter(
        yookassa_status__in=['pending', 'waiting_for_capture'],
        yookassa_id__isnull=False
    ).select_related('contract')

    updated_count = 0
    for payment in pending_payments:
        try:
            # Запрашиваем актуальный статус из ЮKassa
            yoo_payment = YooPayment.find_one(payment.yookassa_id)
            new_status = yoo_payment.status
            if new_status != payment.yookassa_status:
                payment.yookassa_status = new_status
                if new_status == 'succeeded':
                    payment.paid_at = timezone.now()
                    payment.save()
                    # Обновляем контракт (сигнал post_save сделает это автоматически)
                    # Но можно вызвать обновление явно
                    contract = payment.contract
                    contract.save()  # пересчитает paid_amount и payment_status
                    # Отправляем уведомления (отдельная задача)
                    send_payment_success_notifications.delay(payment.id)
                elif new_status == 'canceled':
                    payment.save()
                updated_count += 1
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            print(f"Ошибка при проверке платежа {payment.yookassa_id}: {e}")

    return f"Проверено {pending_payments.count()} платежей, обновлено {updated_count}"


@shared_task
def send_payment_success_notifications(payment_id):
    """Отправка уведомлений менеджеру и клиенту об успешной оплате"""
    from notifications.models import Notification
    from django.core.mail import send_mail
    from django.conf import settings

    try:
        payment = Payment.objects.select_related('contract__manager', 'contract__client').get(id=payment_id)
        contract = payment.contract
        amount = payment.amount
    except Payment.DoesNotExist:
        return

    # Уведомление менеджеру
    if contract.manager:
        Notification.objects.create(
            user=contract.manager,
            type='success',
            title=f'Поступила оплата по контракту {contract.number}',
            message=f'Оплата на сумму {amount} ₽ по контракту {contract.number} (клиент {contract.client.full_name}) успешно проведена.',
            link=f'/contracts/{contract.id}/'
        )
        # Email менеджеру, если включены уведомления
        prefs = getattr(contract.manager, 'notification_prefs', None)
        if prefs and prefs.email_enabled:
            send_mail(
                subject=f'Оплата по контракту {contract.number}',
                message=f'Здравствуйте, {contract.manager.get_full_name()}!\n\nПо контракту {contract.number} поступила оплата {amount} ₽.\n\nСсылка: {settings.BASE_URL}/contracts/{contract.id}/',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contract.manager.email],
                fail_silently=True,
            )

    # Уведомление клиенту (если у клиента есть email)
    if contract.client and contract.client.email:
        # Создаём уведомление в системе (для клиента как пользователя? в модели Client нет связи с User,
        # поэтому отправляем только email)
        send_mail(
            subject=f'Оплата по контракту {contract.number}',
            message=f'Уважаемый клиент!\n\nПо контракту {contract.number} на сумму {contract.amount} ₽ зафиксирована оплата {amount} ₽.\n\nСпасибо за сотрудничество!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[contract.client.email],
            fail_silently=True,
        )

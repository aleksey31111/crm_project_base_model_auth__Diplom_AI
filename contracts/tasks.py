from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from yookassa import Configuration, Payment as YooPayment


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


@shared_task
def check_payment_status():
    """Периодически проверяет статус неоплаченных платежей в ЮKassa"""
    if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
        return

    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

    pending_payments = Payment.objects.filter(
        yookassa_status__in=['pending', 'waiting_for_capture'],
        yookassa_id__isnull=False
    ).select_related('contract')

    for payment in pending_payments:
        try:
            yoo_payment = YooPayment.find_one(payment.yookassa_id)
            if yoo_payment.status == 'succeeded':
                payment.yookassa_status = 'succeeded'
                payment.paid_at = timezone.now()
                payment.save()
                # Обновляем контракт (через сигнал или вручную)
                contract = payment.contract
                contract.paid_amount += payment.amount
                contract.save()
            elif yoo_payment.status == 'canceled':
                payment.yookassa_status = 'canceled'
                payment.save()
        except Exception as e:
            print(f"Error checking payment {payment.yookassa_id}: {e}")

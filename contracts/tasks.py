from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

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
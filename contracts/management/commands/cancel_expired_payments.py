from django.core.management.base import BaseCommand
from django.utils import timezone
from yookassa import Payment as YooPayment
from contracts.models import Payment

class Command(BaseCommand):
    help = 'Отменяет просроченные платежи в ЮKassa и обновляет статус в системе'

    def handle(self, *args, **options):
        now = timezone.now()
        # Ищем платежи, у которых истёк срок действия ссылки, статус ещё pending
        expired_payments = Payment.objects.filter(
            yookassa_status='pending',
            contract__payment_expires_at__lt=now,
            yookassa_id__isnull=False
        ).select_related('contract')

        count = 0
        for payment in expired_payments:
            try:
                # Отменяем платеж через API ЮKassa
                yoo_payment = YooPayment.find_one(payment.yookassa_id)
                if yoo_payment.status == 'pending':
                    yoo_payment.cancel()
                payment.yookassa_status = 'canceled'
                payment.save()
                count += 1
                self.stdout.write(f"Отменён платёж {payment.yookassa_id} по контракту {payment.contract.number}")
            except Exception as e:
                self.stderr.write(f"Ошибка при отмене {payment.yookassa_id}: {e}")

        self.stdout.write(self.style.SUCCESS(f'Отменено {count} просроченных платежей.'))

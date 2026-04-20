from django.core.management.base import BaseCommand
from django.utils import timezone
from contracts.models import Contract, Payment
from yookassa import Configuration, Payment as YooPayment
from django.conf import settings

class Command(BaseCommand):
    help = 'Отменяет просроченные неоплаченные платежи в ЮKassa'

    def handle(self, *args, **options):
        if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
            self.stdout.write(self.style.ERROR('ЮKassa не настроена'))
            return

        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

        # Платежи, у которых истёк срок действия ссылки
        expired_payments = Payment.objects.filter(
            yookassa_status='pending',
            contract__payment_expires_at__lt=timezone.now(),
            yookassa_id__isnull=False
        ).select_related('contract')

        count = 0
        for payment in expired_payments:
            try:
                YooPayment.cancel(payment.yookassa_id)
                payment.yookassa_status = 'canceled'
                payment.save()
                count += 1
                self.stdout.write(f'Отменён платёж {payment.yookassa_id}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка отмены {payment.yookassa_id}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Отменено {count} платежей'))
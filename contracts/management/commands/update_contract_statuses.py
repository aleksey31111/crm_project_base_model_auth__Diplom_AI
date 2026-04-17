from django.core.management.base import BaseCommand
from contracts.models import Contract

class Command(BaseCommand):
    help = 'Обновляет статусы контрактов на основе дат'

    def handle(self, *args, **options):
        contracts = Contract.objects.all()
        updated = 0
        for contract in contracts:
            old_status = contract.status
            contract.save()  # вызовет обновление статуса
            if contract.status != old_status:
                updated += 1
                self.stdout.write(f'Обновлён {contract.number}: {old_status} → {contract.status}')
        self.stdout.write(self.style.SUCCESS(f'Обновлено {updated} контрактов.'))
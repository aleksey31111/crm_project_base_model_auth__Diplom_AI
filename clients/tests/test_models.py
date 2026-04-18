from django.test import TestCase
from django.contrib.auth import get_user_model
from clients.models import Client
from contracts.models import Contract
from datetime import date

User = get_user_model()

class ClientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='manager', password='pass', role='MANAGER')
        self.client = Client.objects.create(
            full_name='ООО Тест',
            inn='123456789012',
            manager=self.user,
            status='active'
        )

    def test_client_creation(self):
        self.assertEqual(self.client.full_name, 'ООО Тест')
        self.assertEqual(self.client.inn, '123456789012')
        self.assertTrue(self.client.is_active)

    def test_client_str_method(self):
        self.assertEqual(str(self.client), 'ООО Тест')

    def test_client_full_address(self):
        self.client.country = 'Россия'
        self.client.city = 'Москва'
        self.client.address = 'ул. Ленина, 1'
        self.assertEqual(self.client.full_address, 'Россия, Москва, ул. Ленина, 1')

    def test_contract_relation(self):
        contract = Contract.objects.create(
            client=self.client,
            number='C-001',
            title='Тестовый контракт',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            amount=100000,
            manager=self.user
        )
        self.assertEqual(self.client.contracts.count(), 1)
        self.assertEqual(self.client.contracts.first(), contract)

    def test_client_logo_field(self):
        # По умолчанию поле logo пустое (None в БД)
        # В Django пустое поле возвращает объект, у которого .name == None
        self.assertIsNone(self.client.logo.name)

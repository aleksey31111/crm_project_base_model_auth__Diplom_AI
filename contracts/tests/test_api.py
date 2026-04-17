from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from clients.models import Client
from contracts.models import Contract

User = get_user_model()

class ContractAPITest(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='manager', password='pass', role='MANAGER')
        self.client_obj = Client.objects.create(full_name='Клиент', manager=self.manager)
        self.contract = Contract.objects.create(
            client=self.client_obj,
            number='C-001',
            title='Тестовый контракт',
            start_date='2025-01-01',
            end_date='2025-12-31',
            amount=50000,
            manager=self.manager
        )

    def test_list_contracts_as_manager(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/contracts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_contract_payment_percentage(self):
        self.contract.paid_amount = 25000
        self.contract.save()
        self.assertEqual(self.contract.payment_percentage, 50.0)

    def test_remaining_amount_property(self):
        self.contract.paid_amount = 15000
        self.assertEqual(self.contract.remaining_amount, 35000)

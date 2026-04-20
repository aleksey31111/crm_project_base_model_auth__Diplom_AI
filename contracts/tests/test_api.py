from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from clients.models import Client
from contracts.models import Contract
from datetime import date, timedelta

User = get_user_model()

class ContractAPITest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpass'
        )
        self.manager = User.objects.create_user(
            username='manager',
            password='managerpass',
            role='MANAGER'
        )
        self.other_manager = User.objects.create_user(
            username='other_manager',
            password='otherpass',
            role='MANAGER'
        )
        self.viewer = User.objects.create_user(
            username='viewer',
            password='viewerpass',
            role='VIEWER'
        )

        self.client_own = Client.objects.create(
            full_name='Клиент менеджера',
            manager=self.manager,
            status='active'
        )
        self.client_other = Client.objects.create(
            full_name='Клиент другого менеджера',
            manager=self.other_manager,
            status='active'
        )

        today = date.today()
        self.contract_own = Contract.objects.create(
            client=self.client_own,
            number='C-001',
            title='Контракт менеджера',
            start_date=today,
            end_date=today + timedelta(days=365),
            amount=100000,
            manager=self.manager,
            status='active'
        )
        self.contract_other = Contract.objects.create(
            client=self.client_other,
            number='C-002',
            title='Чужой контракт',
            start_date=today,
            end_date=today + timedelta(days=365),
            amount=200000,
            manager=self.other_manager,
            status='active'
        )

    def test_unauthenticated_cannot_access(self):
        response = self.client.get('/api/contracts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manager_sees_only_own_contracts(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/contracts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['number'], 'C-001')

    def test_admin_sees_all_contracts(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/contracts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_viewer_cannot_create_contract(self):
        self.client.force_authenticate(user=self.viewer)
        data = {
            'client': self.client_own.id,
            'number': 'C-003',
            'title': 'Новый контракт',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'amount': 50000,
        }
        response = self.client.post('/api/contracts/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_create_contract(self):
        self.client.force_authenticate(user=self.manager)
        data = {
            'client': self.client_own.id,
            'number': 'C-003',
            'title': 'Новый контракт',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'amount': 50000,
        }
        response = self.client.post('/api/contracts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contract.objects.count(), 3)
        self.assertEqual(response.data['manager'], self.manager.id)

    def test_manager_can_update_own_contract(self):
        self.client.force_authenticate(user=self.manager)
        url = f'/api/contracts/{self.contract_own.id}/'
        response = self.client.patch(url, {'title': 'Обновлённое название'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.contract_own.refresh_from_db()
        self.assertEqual(self.contract_own.title, 'Обновлённое название')

    def test_manager_cannot_update_other_contract(self):
        self.client.force_authenticate(user=self.manager)
        url = f'/api/contracts/{self.contract_other.id}/'
        response = self.client.patch(url, {'title': 'Попытка взлома'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_contract_serializer_contains_readonly_fields(self):
        self.client.force_authenticate(user=self.manager)
        url = f'/api/contracts/{self.contract_own.id}/'
        response = self.client.get(url)
        self.assertIn('remaining_amount', response.data)
        self.assertIn('payment_percentage', response.data)
        self.assertIn('payments', response.data)
        self.assertEqual(float(response.data['remaining_amount']), 100000.0)
        self.assertEqual(response.data['payment_percentage'], 0.0)

    def test_filter_contracts_by_status(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/contracts/?status=active')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_search_contracts_by_number(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/contracts/?search=C-001')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['number'], 'C-001')

    def test_payment_percentage_calculation(self):
        self.contract_own.paid_amount = 25000
        self.contract_own.save()
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(f'/api/contracts/{self.contract_own.id}/')
        self.assertEqual(response.data['payment_percentage'], 25.0)

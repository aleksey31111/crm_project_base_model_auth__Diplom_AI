from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from clients.models import Client
from contracts.models import Contract, Payment
import json

User = get_user_model()

class PaymentInitiationTest(APITestCase):
    """Тесты для эндпоинта initiate-payment (учебный режим, без реальной ЮKassa)"""

    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        self.manager = User.objects.create_user(username='manager', password='managerpass', role='MANAGER')
        self.viewer = User.objects.create_user(username='viewer', password='viewerpass', role='VIEWER')
        self.client_obj = Client.objects.create(full_name='Клиент', manager=self.manager)
        self.contract = Contract.objects.create(
            client=self.client_obj,
            number='C-001',
            title='Тестовый контракт',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            amount=100000,
            manager=self.manager,
            payment_status='not_paid'
        )

    def test_unauthenticated_cannot_initiate_payment(self):
        url = reverse('contract-initiate-payment', args=[self.contract.id])
        response = self.client.post(url, {'amount': 5000})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_viewer_cannot_initiate_payment(self):
        self.client.force_authenticate(user=self.viewer)
        url = reverse('contract-initiate-payment', args=[self.contract.id])
        response = self.client.post(url, {'amount': 5000})
        # Зритель не имеет доступа к контрактам вообще (404)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_can_initiate_payment_for_own_contract(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('contract-initiate-payment', args=[self.contract.id])
        response = self.client.post(url, {'amount': 5000})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('confirmation_url', response.data)
        self.assertTrue(response.data['confirmation_url'].startswith('/fake-payment/'))
        self.assertEqual(response.data['amount'], '5000.00')
        self.contract.refresh_from_db()
        self.assertIsNotNone(self.contract.yookassa_payment_id)
        self.assertIsNotNone(self.contract.payment_url)
        self.assertTrue(Payment.objects.filter(contract=self.contract, amount=5000).exists())

    def test_initiate_payment_without_amount_uses_remaining_amount(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('contract-initiate-payment', args=[self.contract.id])
        self.contract.paid_amount = 20000
        self.contract.save()
        remaining = self.contract.remaining_amount  # 80000
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], f'{remaining:.2f}')

    def test_initiate_payment_with_amount_greater_than_remaining(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('contract-initiate-payment', args=[self.contract.id])
        response = self.client.post(url, {'amount': 150000})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('превышать остаток', response.data['error'])

    def test_initiate_payment_for_already_paid_contract(self):
        self.contract.paid_amount = 100000
        self.contract.save()
        self.client.force_authenticate(user=self.manager)
        url = reverse('contract-initiate-payment', args=[self.contract.id])
        response = self.client.post(url, {'amount': 10000})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('полностью оплачен', response.data['error'])

    def test_initiate_payment_with_negative_amount(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('contract-initiate-payment', args=[self.contract.id])
        response = self.client.post(url, {'amount': -100})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('положительной', response.data['error'])

    def test_manager_cannot_initiate_payment_for_other_contract(self):
        other_manager = User.objects.create_user(username='other', password='otherpass', role='MANAGER')
        other_client = Client.objects.create(full_name='Другой', manager=other_manager)
        other_contract = Contract.objects.create(
            client=other_client,
            number='C-002',
            title='Чужой',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            amount=50000,
            manager=other_manager
        )
        self.client.force_authenticate(user=self.manager)
        url = reverse('contract-initiate-payment', args=[other_contract.id])
        response = self.client.post(url, {'amount': 1000})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FakeWebhookTest(APITestCase):
    """Тесты для внутреннего вебхука (имитация получения уведомления об оплате)"""

    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        self.manager = User.objects.create_user(username='manager', password='managerpass', role='MANAGER')
        self.client_obj = Client.objects.create(full_name='Клиент', manager=self.manager)
        self.contract = Contract.objects.create(
            client=self.client_obj,
            number='C-001',
            title='Тестовый контракт',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            amount=100000,
            manager=self.manager,
            paid_amount=0
        )
        self.payment = Payment.objects.create(
            contract=self.contract,
            amount=50000,
            payment_date=date.today(),
            yookassa_id='fake_123',
            yookassa_status='pending',
            created_by=self.manager
        )
        self.webhook_url = reverse('contracts:yookassa_webhook')

    def test_webhook_successful_payment_updates_payment_and_contract(self):
        data = {
            "event": "payment.succeeded",
            "object": {
                "id": "fake_123",
                "status": "succeeded"
            }
        }
        response = self.client.post(self.webhook_url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.yookassa_status, 'succeeded')
        self.assertIsNotNone(self.payment.paid_at)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.paid_amount, 50000)
        self.assertEqual(self.contract.payment_status, 'partially_paid')

    def test_webhook_full_payment_marks_contract_paid(self):
        self.payment.amount = 100000
        self.payment.save()
        data = {
            "event": "payment.succeeded",
            "object": {
                "id": "fake_123",
                "status": "succeeded"
            }
        }
        response = self.client.post(self.webhook_url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.paid_amount, 100000)
        self.assertEqual(self.contract.payment_status, 'paid')

    def test_webhook_canceled_payment_updates_status(self):
        data = {
            "event": "payment.canceled",
            "object": {
                "id": "fake_123",
                "status": "canceled"
            }
        }
        response = self.client.post(self.webhook_url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.yookassa_status, 'canceled')
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.paid_amount, 0)

    def test_webhook_unknown_payment_id_returns_404(self):
        data = {
            "event": "payment.succeeded",
            "object": {"id": "unknown_id", "status": "succeeded"}
        }
        response = self.client.post(self.webhook_url, data, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_webhook_invalid_event_returns_400(self):
        data = {"event": "unknown.event", "object": {"id": "fake_123"}}
        response = self.client.post(self.webhook_url, data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_webhook_invalid_json_returns_400(self):
        response = self.client.post(self.webhook_url, 'not json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_webhook_wrong_method_returns_405(self):
        response = self.client.get(self.webhook_url)
        self.assertEqual(response.status_code, 405)


class PaymentPermissionsTest(APITestCase):
    """Дополнительные тесты прав доступа к платежам"""

    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        self.manager = User.objects.create_user(username='manager', password='managerpass', role='MANAGER')
        self.other_manager = User.objects.create_user(username='other', password='otherpass', role='MANAGER')
        self.client_obj = Client.objects.create(full_name='Клиент', manager=self.manager)
        self.contract = Contract.objects.create(
            client=self.client_obj,
            number='C-001',
            title='Тестовый контракт',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            amount=100000,
            manager=self.manager
        )
        self.payment = Payment.objects.create(
            contract=self.contract,
            amount=10000,
            payment_date=date.today(),
            created_by=self.manager
        )

    def test_admin_can_view_all_payments(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/payments/')
        self.assertEqual(response.status_code, 200)

    def test_manager_cannot_view_other_payments(self):
        self.client.force_authenticate(user=self.other_manager)
        response = self.client.get(f'/api/payments/{self.payment.id}/')
        self.assertEqual(response.status_code, 404)

    def test_manager_can_view_own_contract_payment(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(f'/api/contracts/{self.contract.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['payments']), 1)

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from clients.models import Client
from contracts.models import Contract

User = get_user_model()


class ClientAPITest(APITestCase):
    """Тесты API для модели Client"""

    def setUp(self):
        # Создаём пользователей
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com'
        )
        self.manager = User.objects.create_user(
            username='manager',
            password='managerpass',
            role='MANAGER',
            email='manager@example.com'
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

        # Создаём клиентов
        self.client1 = Client.objects.create(
            full_name='Клиент менеджера',
            manager=self.manager,
            status='active'
        )
        self.client2 = Client.objects.create(
            full_name='Клиент другого менеджера',
            manager=self.other_manager,
            status='inactive'
        )
        self.client3 = Client.objects.create(
            full_name='Клиент без ответственного',  # изменено название
            manager=None,
            status='active'
        )

    def test_unauthenticated_cannot_access(self):
        """Неаутентифицированный пользователь не может получить список клиентов"""
        response = self.client.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manager_sees_only_own_clients(self):
        """Менеджер видит только своих клиентов"""
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['full_name'], 'Клиент менеджера')

    def test_admin_sees_all_clients(self):
        """Администратор видит всех клиентов"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_viewer_sees_no_clients(self):
        """Пользователь с ролью VIEWER не видит клиентов (т.к. у него нет manager)"""
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_manager_can_create_client(self):
        """Менеджер может создать клиента"""
        self.client.force_authenticate(user=self.manager)
        data = {
            'full_name': 'Новый клиент',
            'type': 'company',
            'status': 'active'
        }
        response = self.client.post('/api/clients/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Client.objects.count(), 4)
        self.assertEqual(response.data['manager'], self.manager.id)

    def test_manager_can_update_own_client(self):
        """Менеджер может обновить своего клиента"""
        self.client.force_authenticate(user=self.manager)
        url = f'/api/clients/{self.client1.id}/'
        response = self.client.patch(url, {'full_name': 'Обновлённый клиент'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client1.refresh_from_db()
        self.assertEqual(self.client1.full_name, 'Обновлённый клиент')

    def test_manager_cannot_update_other_client(self):
        """Менеджер не может обновить чужого клиента"""
        self.client.force_authenticate(user=self.manager)
        url = f'/api/clients/{self.client2.id}/'
        response = self.client.patch(url, {'full_name': 'Попытка взлома'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_update_any_client(self):
        """Администратор может обновить любого клиента"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/clients/{self.client2.id}/'
        response = self.client.patch(url, {'full_name': 'Исправлено админом'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client2.refresh_from_db()
        self.assertEqual(self.client2.full_name, 'Исправлено админом')

    def test_search_clients_by_name(self):
        """Поиск клиентов по названию"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/clients/?search=менеджера')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # client1 и client2

    def test_filter_clients_by_status(self):
        """Фильтрация клиентов по статусу"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/clients/?status=active')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # client1 и client3
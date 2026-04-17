from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from clients.models import Client

User = get_user_model()

class ClientAPITest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        self.manager = User.objects.create_user(username='manager', password='pass', role='MANAGER')
        self.client_obj = Client.objects.create(
            full_name='Клиент менеджера',
            manager=self.manager
        )

    def test_unauthenticated_cannot_access(self):
        response = self.client.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manager_sees_own_clients(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['full_name'], 'Клиент менеджера')

    def test_admin_sees_all_clients(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_client_as_manager(self):
        self.client.force_authenticate(user=self.manager)
        data = {'full_name': 'Новый клиент', 'type': 'company'}
        response = self.client.post('/api/clients/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Client.objects.count(), 2)

    def test_update_own_client(self):
        self.client.force_authenticate(user=self.manager)
        url = f'/api/clients/{self.client_obj.id}/'
        response = self.client.patch(url, {'full_name': 'Изменённый клиент'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.full_name, 'Изменённый клиент')

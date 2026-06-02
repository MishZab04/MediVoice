from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User, UserRole


class UserModelTest(APITestCase):
    def test_create_user_defaults_to_health_worker(self):
        user = User.objects.create_user(
            email='worker@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe',
        )
        self.assertEqual(user.email, 'worker@test.com')
        self.assertEqual(user.role, UserRole.HEALTH_WORKER)
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_superuser)

    def test_create_superuser_sets_admin_role(self):
        admin = User.objects.create_superuser(
            email='admin@test.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.role, UserRole.ADMIN)

    def test_email_is_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='pass')


class LoginTest(APITestCase):
    def setUp(self):
        self.url = reverse('authentication:login')
        self.user = User.objects.create_superuser(
            email='admin@test.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
        )

    def test_login_returns_tokens_and_user(self):
        response = self.client.post(self.url, {'email': 'admin@test.com', 'password': 'adminpass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'admin@test.com')

    def test_login_fails_with_wrong_password(self):
        response = self.client.post(self.url, {'email': 'admin@test.com', 'password': 'wrongpass'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_fails_with_unknown_email(self):
        response = self.client.post(self.url, {'email': 'nobody@test.com', 'password': 'pass'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileTest(APITestCase):
    def setUp(self):
        self.url = reverse('authentication:profile')
        self.user = User.objects.create_superuser(
            email='admin@test.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
        )

    def test_me_returns_profile_when_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'admin@test.com')

    def test_me_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class HealthWorkerManagementTest(APITestCase):
    def setUp(self):
        self.list_url = reverse('authentication:health-workers-list')
        self.admin = User.objects.create_superuser(
            email='admin@test.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
        )
        self.worker = User.objects.create_user(
            email='worker@test.com',
            password='workerpass123',
            first_name='Jane',
            last_name='Doe',
            role=UserRole.HEALTH_WORKER,
        )

    def test_admin_can_list_health_workers(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_worker_cannot_list_users(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_health_worker(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            'email': 'new.worker@test.com',
            'first_name': 'New',
            'last_name': 'Worker',
            'password': 'newpass123',
            'facility_name': 'Yaoundé Central',
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='new.worker@test.com').exists())

    def test_unauthenticated_cannot_access(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

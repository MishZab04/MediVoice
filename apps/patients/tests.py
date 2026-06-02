from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User, UserRole
from .models import Patient


def make_health_worker(email='worker@test.com', **kwargs):
    return User.objects.create_user(
        email=email, password='testpass123',
        first_name='Jane', last_name='Doe',
        role=UserRole.HEALTH_WORKER, **kwargs,
    )


def make_admin():
    return User.objects.create_superuser(
        email='admin@test.com', password='adminpass123',
        first_name='Admin', last_name='User',
    )


def make_patient(health_worker, **kwargs):
    defaults = {
        'first_name': 'John', 'last_name': 'Mbu',
        'sex': 'male', 'language_preference': 'en',
    }
    defaults.update(kwargs)
    return Patient.objects.create(health_worker=health_worker, **defaults)


class PatientCreateListTest(APITestCase):
    def setUp(self):
        self.url = reverse('patients:patients-list')
        self.worker = make_health_worker()
        self.admin = make_admin()

    def test_health_worker_can_create_patient(self):
        self.client.force_authenticate(user=self.worker)
        data = {
            'first_name': 'Paul', 'last_name': 'Biya',
            'sex': 'male', 'language_preference': 'fr',
            'location': 'Yaoundé',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Patient.objects.first().health_worker, self.worker)

    def test_create_response_returns_full_detail(self):
        self.client.force_authenticate(user=self.worker)
        data = {'first_name': 'Paul', 'last_name': 'Biya', 'sex': 'male'}
        response = self.client.post(self.url, data)
        self.assertIn('id', response.data)
        self.assertIn('full_name', response.data)
        self.assertIn('health_worker_name', response.data)

    def test_health_worker_sees_only_own_patients(self):
        other_worker = make_health_worker(email='other@test.com')
        make_patient(self.worker)
        make_patient(other_worker)
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_admin_sees_all_patients(self):
        other_worker = make_health_worker(email='other@test.com')
        make_patient(self.worker)
        make_patient(other_worker)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_unauthenticated_cannot_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_by_name(self):
        make_patient(self.worker, first_name='Marie', last_name='Fouda')
        make_patient(self.worker, first_name='Pierre', last_name='Nkodo')
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(self.url, {'search': 'Marie'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['first_name'], 'Marie')


class PatientDetailTest(APITestCase):
    def setUp(self):
        self.worker = make_health_worker()
        self.other_worker = make_health_worker(email='other@test.com')
        self.admin = make_admin()
        self.patient = make_patient(self.worker)
        self.url = reverse('patients:patients-detail', kwargs={'pk': self.patient.pk})

    def test_owner_can_retrieve_patient(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')

    def test_other_worker_cannot_retrieve_patient(self):
        # Returns 404, not 403 — queryset scoping hides other workers' patients entirely
        self.client.force_authenticate(user=self.other_worker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_retrieve_any_patient(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_can_update_patient(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.patch(self.url, {'location': 'Douala'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.location, 'Douala')

    def test_update_response_returns_full_detail(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.patch(self.url, {'location': 'Douala'})
        self.assertIn('full_name', response.data)
        self.assertIn('health_worker_name', response.data)

    def test_other_worker_cannot_update_patient(self):
        self.client.force_authenticate(user=self.other_worker)
        response = self.client.patch(self.url, {'location': 'Douala'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_soft_deactivates_patient(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.is_active)
        self.assertTrue(Patient.objects.filter(pk=self.patient.pk).exists())

    def test_other_worker_cannot_delete_patient(self):
        self.client.force_authenticate(user=self.other_worker)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_update_any_patient(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(self.url, {'location': 'Bafoussam'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.location, 'Bafoussam')

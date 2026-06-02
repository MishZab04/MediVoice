from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User, UserRole
from apps.patients.models import Patient
from services.questionnaire.questions import QUESTION_ORDER
from .models import AssessmentSession, AssessmentResponse, AssessmentStatus


def make_health_worker(email='worker@test.com'):
    return User.objects.create_user(
        email=email, password='testpass123',
        first_name='Jane', last_name='Doe',
        role=UserRole.HEALTH_WORKER,
    )


def make_admin():
    return User.objects.create_superuser(
        email='admin@test.com', password='adminpass123',
        first_name='Admin', last_name='User',
    )


def make_patient(health_worker, **kwargs):
    defaults = {'first_name': 'John', 'last_name': 'Mbu', 'sex': 'male'}
    defaults.update(kwargs)
    return Patient.objects.create(health_worker=health_worker, **defaults)


class StartAssessmentTest(APITestCase):
    def setUp(self):
        self.url = reverse('assessment:start')
        self.worker = make_health_worker()
        self.patient = make_patient(self.worker)

    def test_start_creates_session_and_returns_first_question(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(self.url, {
            'patient_id': str(self.patient.id),
            'language': 'en',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('session_id', response.data)
        self.assertEqual(response.data['question_key'], 'fever')
        self.assertEqual(response.data['question_text'], 'Do you have fever?')
        self.assertIsNone(response.data['audio_url'])

    def test_start_returns_french_question_for_fr_language(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(self.url, {
            'patient_id': str(self.patient.id),
            'language': 'fr',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['question_text'], 'Avez-vous de la fièvre ?')

    def test_start_returns_pidgin_question_for_pcm_language(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(self.url, {
            'patient_id': str(self.patient.id),
            'language': 'pcm',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['question_text'], 'Ya body dey hot?')

    def test_start_session_is_saved_in_progress(self):
        self.client.force_authenticate(user=self.worker)
        self.client.post(self.url, {'patient_id': str(self.patient.id), 'language': 'en'})
        session = AssessmentSession.objects.get()
        self.assertEqual(session.status, AssessmentStatus.IN_PROGRESS)
        self.assertEqual(session.health_worker, self.worker)
        self.assertEqual(session.patient, self.patient)

    def test_worker_cannot_start_session_for_another_workers_patient(self):
        other_worker = make_health_worker(email='other@test.com')
        other_patient = make_patient(other_worker)
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(self.url, {
            'patient_id': str(other_patient.id),
            'language': 'en',
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_start(self):
        response = self.client.post(self.url, {
            'patient_id': str(self.patient.id),
            'language': 'en',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RespondViewTest(APITestCase):
    def setUp(self):
        self.start_url = reverse('assessment:start')
        self.respond_url = reverse('assessment:respond')
        self.worker = make_health_worker()
        self.patient = make_patient(self.worker)
        self.client.force_authenticate(user=self.worker)

        # Start a session to use in tests
        resp = self.client.post(self.start_url, {
            'patient_id': str(self.patient.id),
            'language': 'en',
        })
        self.session_id = resp.data['session_id']

    def test_respond_saves_answer_and_returns_next_question(self):
        response = self.client.post(self.respond_url, {
            'session_id': self.session_id,
            'answer_text': 'Yes I have fever',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['question_key'], 'vomiting')
        self.assertEqual(response.data['question_text'], 'Are you vomiting?')
        self.assertIn('confirmation', response.data)

    def test_respond_saves_response_to_database(self):
        self.client.post(self.respond_url, {
            'session_id': self.session_id,
            'answer_text': 'Yes I have fever',
        })
        self.assertEqual(AssessmentResponse.objects.count(), 1)
        saved = AssessmentResponse.objects.get()
        self.assertEqual(saved.question_key, 'fever')
        self.assertEqual(saved.answer_text, 'Yes I have fever')

    def test_respond_advances_current_question(self):
        self.client.post(self.respond_url, {
            'session_id': self.session_id,
            'answer_text': 'Yes',
        })
        session = AssessmentSession.objects.get(pk=self.session_id)
        self.assertEqual(session.current_question, 'vomiting')

    def test_full_conversation_completes_session(self):
        # Answer all 10 questions
        for i, question_key in enumerate(QUESTION_ORDER):
            response = self.client.post(self.respond_url, {
                'session_id': self.session_id,
                'answer_text': f'Answer to {question_key}',
            })
            if i < len(QUESTION_ORDER) - 1:
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn('question_key', response.data)
            else:
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['status'], 'completed')

        session = AssessmentSession.objects.get(pk=self.session_id)
        self.assertEqual(session.status, AssessmentStatus.COMPLETED)
        self.assertIsNotNone(session.completed_at)
        self.assertEqual(AssessmentResponse.objects.count(), 10)

    def test_completed_session_cannot_receive_more_responses(self):
        for question_key in QUESTION_ORDER:
            self.client.post(self.respond_url, {
                'session_id': self.session_id,
                'answer_text': 'answer',
            })
        # Session is now complete — try to respond again
        response = self.client.post(self.respond_url, {
            'session_id': self.session_id,
            'answer_text': 'extra answer',
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_other_worker_cannot_respond_to_session(self):
        other_worker = make_health_worker(email='other@test.com')
        self.client.force_authenticate(user=other_worker)
        response = self.client.post(self.respond_url, {
            'session_id': self.session_id,
            'answer_text': 'answer',
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SessionDetailTest(APITestCase):
    def setUp(self):
        self.worker = make_health_worker()
        self.patient = make_patient(self.worker)
        self.client.force_authenticate(user=self.worker)

        resp = self.client.post(reverse('assessment:start'), {
            'patient_id': str(self.patient.id),
            'language': 'en',
        })
        self.session_id = resp.data['session_id']
        self.url = reverse('assessment:session-detail', kwargs={'session_id': self.session_id})

    def test_owner_can_retrieve_session(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(self.session_id))
        self.assertIn('responses', response.data)

    def test_other_worker_cannot_retrieve_session(self):
        other_worker = make_health_worker(email='other@test.com')
        self.client.force_authenticate(user=other_worker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

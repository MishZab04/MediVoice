import logging
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import status, serializers as drf_serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsHealthWorker
from apps.patients.models import Patient
from services.questionnaire.flow_engine import get_first_question, get_next_question
from services.questionnaire.questions import get_question_text, get_confirmation
from services.tts.manager import get_audio_url

from .models import AssessmentSession, AssessmentResponse, AssessmentStatus
from .serializers import StartAssessmentSerializer, RespondSerializer, AssessmentSessionSerializer

logger = logging.getLogger('apps.assessment')


class StartAssessmentView(APIView):
    permission_classes = [IsAuthenticated, IsHealthWorker]

    @extend_schema(
        request=StartAssessmentSerializer,
        responses={
            201: inline_serializer('StartResponse', fields={
                'session_id': drf_serializers.UUIDField(),
                'question_key': drf_serializers.CharField(),
                'question_text': drf_serializers.CharField(),
                'audio_url': drf_serializers.CharField(allow_null=True),
            }),
        },
        summary='Start a new assessment session',
        description='Creates a new AssessmentSession for a patient and returns the first question. The health worker must own the patient.',
    )
    def post(self, request):
        serializer = StartAssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        patient_id = serializer.validated_data['patient_id']
        language = serializer.validated_data['language']

        # Verify the patient belongs to this health worker (or user is admin)
        qs = Patient.objects.filter(pk=patient_id, is_active=True)
        if not request.user.is_admin:
            qs = qs.filter(health_worker=request.user)

        try:
            patient = qs.get()
        except Patient.DoesNotExist:
            return Response(
                {'detail': 'Patient not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        first_question = get_first_question()

        session = AssessmentSession.objects.create(
            patient=patient,
            health_worker=request.user,
            language=language,
            current_question=first_question,
            status=AssessmentStatus.IN_PROGRESS,
        )

        logger.info('Assessment session %s started by %s', session.id, request.user.email)

        return Response({
            'session_id': session.id,
            'question_key': first_question,
            'question_text': get_question_text(first_question, language),
            'audio_url': get_audio_url(first_question, language),
        }, status=status.HTTP_201_CREATED)


class RespondView(APIView):
    permission_classes = [IsAuthenticated, IsHealthWorker]

    @extend_schema(
        request=RespondSerializer,
        responses={
            200: inline_serializer('RespondResponse', fields={
                'session_id': drf_serializers.UUIDField(),
                'question_key': drf_serializers.CharField(),
                'question_text': drf_serializers.CharField(),
                'confirmation': drf_serializers.CharField(),
                'audio_url': drf_serializers.CharField(allow_null=True),
                'status': drf_serializers.CharField(),
            }),
        },
        summary='Submit an answer and get the next question',
        description='Accepts the patient\'s answer for the current question, saves it, and returns the next question. Returns status=completed when all questions are answered.',
    )
    def post(self, request):
        serializer = RespondSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data['session_id']
        answer_text = serializer.validated_data['answer_text']

        # Fetch the session — health workers can only access their own sessions
        qs = AssessmentSession.objects.filter(
            pk=session_id,
            status=AssessmentStatus.IN_PROGRESS,
        )
        if not request.user.is_admin:
            qs = qs.filter(health_worker=request.user)

        try:
            session = qs.get()
        except AssessmentSession.DoesNotExist:
            return Response(
                {'detail': 'Active session not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        current_key = session.current_question

        # Save the response for the current question
        AssessmentResponse.objects.create(
            session=session,
            question_key=current_key,
            answer_text=answer_text,
            extracted_value=None,  # NLP extraction added in Phase 8
        )

        logger.info(
            'Session %s — response saved for question "%s"',
            session.id, current_key,
        )

        # Advance to next question
        next_key = get_next_question(current_key)

        if next_key is None:
            # Assessment complete
            session.status = AssessmentStatus.COMPLETED
            session.completed_at = timezone.now()
            session.current_question = current_key
            session.save(update_fields=['status', 'completed_at'])
            logger.info('Assessment session %s completed', session.id)
            return Response({
                'status': 'completed',
                'session_id': session.id,
                'confirmation': get_confirmation(session.language),
            })

        # Move to next question
        session.current_question = next_key
        session.save(update_fields=['current_question'])

        return Response({
            'session_id': session.id,
            'question_key': next_key,
            'question_text': get_question_text(next_key, session.language),
            'confirmation': get_confirmation(session.language),
            'audio_url': get_audio_url(next_key, session.language),
        })


class SessionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsHealthWorker]

    @extend_schema(
        responses={200: AssessmentSessionSerializer},
        summary='Get full session detail',
        description='Returns the full assessment session including all recorded responses.',
    )
    def get(self, request, session_id):
        qs = AssessmentSession.objects.prefetch_related('responses')
        if not request.user.is_admin:
            qs = qs.filter(health_worker=request.user)

        try:
            session = qs.get(pk=session_id)
        except AssessmentSession.DoesNotExist:
            return Response(
                {'detail': 'Session not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(AssessmentSessionSerializer(session).data)

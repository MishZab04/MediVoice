import logging
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessment.models import AssessmentSession, AssessmentStatus, AssessmentPriority
from apps.authentication.models import User, UserRole
from apps.patients.models import Patient

from .serializers import SummarySerializer, DailyCountSerializer

logger = logging.getLogger('apps.analytics')


def _base_qs(user):
    """Return the AssessmentSession queryset scoped to the requesting user."""
    if user.role == UserRole.ADMIN:
        return AssessmentSession.objects.all()
    return AssessmentSession.objects.filter(health_worker=user)


def _patient_qs(user):
    if user.role == UserRole.ADMIN:
        return Patient.objects.all()
    return Patient.objects.filter(health_worker=user)


class SummaryView(APIView):
    """
    GET /api/v1/analytics/summary/

    Dashboard summary statistics.
    - Admin: system-wide totals + top health workers list.
    - Health worker: scoped to their own patients and sessions.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: SummarySerializer},
        summary='Dashboard summary statistics',
    )
    def get(self, request):
        user = request.user
        sessions = _base_qs(user)
        week_ago = timezone.now() - timedelta(days=7)

        by_language = {
            'en':  sessions.filter(language='en').count(),
            'fr':  sessions.filter(language='fr').count(),
            'pcm': sessions.filter(language='pcm').count(),
        }

        by_status = {
            'completed':   sessions.filter(status=AssessmentStatus.COMPLETED).count(),
            'in_progress': sessions.filter(status=AssessmentStatus.IN_PROGRESS).count(),
            'abandoned':   sessions.filter(status=AssessmentStatus.ABANDONED).count(),
        }

        data = {
            'total_assessments':   sessions.count(),
            'total_patients':      _patient_qs(user).count(),
            'total_urgent':        sessions.filter(assessment_priority=AssessmentPriority.URGENT).count(),
            'completed_this_week': sessions.filter(
                status=AssessmentStatus.COMPLETED,
                completed_at__gte=week_ago,
            ).count(),
            'by_language': by_language,
            'by_status':   by_status,
            'total_health_workers': None,
            'top_health_workers':   None,
        }

        if user.role == UserRole.ADMIN:
            data['total_health_workers'] = User.objects.filter(
                role=UserRole.HEALTH_WORKER,
                is_active=True,
            ).count()

            top = (
                User.objects
                .filter(role=UserRole.HEALTH_WORKER)
                .annotate(assessment_count=Count('assessment_sessions'))
                .order_by('-assessment_count')[:5]
            )
            data['top_health_workers'] = [
                {
                    'id':               w.id,
                    'name':             w.get_full_name() or w.email,
                    'email':            w.email,
                    'facility_name':    w.facility_name,
                    'assessment_count': w.assessment_count,
                }
                for w in top
            ]

        serializer = SummarySerializer(data)
        return Response(serializer.data)


class DailyBreakdownView(APIView):
    """
    GET /api/v1/analytics/daily/?days=30

    Completed assessments per day for the last N days (default 30, max 90).
    Useful for rendering a trend chart on the dashboard.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='days',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of past days to include (default 30, max 90)',
                required=False,
            )
        ],
        responses={200: DailyCountSerializer(many=True)},
        summary='Completed assessments per day',
    )
    def get(self, request):
        try:
            days = min(int(request.query_params.get('days', 30)), 90)
        except ValueError:
            days = 30

        since = timezone.now() - timedelta(days=days)
        sessions = _base_qs(request.user).filter(
            status=AssessmentStatus.COMPLETED,
            completed_at__gte=since,
        )

        counts_qs = (
            sessions
            .extra(select={'day': "DATE(completed_at)"})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        result = [{'date': row['day'], 'count': row['count']} for row in counts_qs]
        serializer = DailyCountSerializer(result, many=True)
        return Response(serializer.data)

import logging
import os

from django.conf import settings
from django.http import FileResponse, HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessment.models import AssessmentSession, AssessmentStatus
from apps.authentication.permissions import IsHealthWorker
from services.reports.pdf_generator import generate_assessment_pdf, save_assessment_pdf

logger = logging.getLogger('apps.reports')

REPORTS_DIR = os.path.join(settings.MEDIA_ROOT, 'reports')


class AssessmentReportPDFView(APIView):
    permission_classes = [IsAuthenticated, IsHealthWorker]

    @extend_schema(
        summary='Generate assessment report PDF',
        description=(
            'Generates a PDF clinical assessment report for a completed session. '
            'Saves the file to media/reports/ and also returns it as a download. '
            'Only completed sessions can generate a report.'
        ),
        responses={200: bytes},
    )
    def get(self, request, session_id):
        qs = AssessmentSession.objects.select_related('patient', 'health_worker').filter(
            pk=session_id,
            status=AssessmentStatus.COMPLETED,
        )
        if not request.user.is_admin:
            qs = qs.filter(health_worker=request.user)

        try:
            session = qs.get()
        except AssessmentSession.DoesNotExist:
            return Response(
                {'detail': 'Completed session not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not session.assessment_report:
            return Response(
                {'detail': 'No assessment report available for this session.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Save to media/reports/
            filepath = save_assessment_pdf(session, REPORTS_DIR)
            filename = os.path.basename(filepath)
            media_url = f"{settings.MEDIA_URL}reports/{filename}"

            # Also return as a direct file download
            pdf_bytes = open(filepath, 'rb').read()
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-PDF-URL'] = media_url

            logger.info('PDF report generated for session %s by %s', session_id, request.user.email)
            return response

        except Exception as exc:
            logger.error('PDF generation failed for session %s: %s', session_id, exc)
            return Response(
                {'detail': f'PDF generation failed: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

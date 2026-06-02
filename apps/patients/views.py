import logging
from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.models import UserRole
from apps.authentication.permissions import IsHealthWorker
from .models import Patient
from .serializers import PatientSerializer, PatientWriteSerializer
from .permissions import IsPatientOwner

logger = logging.getLogger('apps.patients')


class PatientViewSet(viewsets.ModelViewSet):
    """
    Patient CRUD.

    GET    /api/v1/patients/        — list (health worker: own patients; admin: all)
    POST   /api/v1/patients/        — create (health worker only)
    GET    /api/v1/patients/{id}/   — detail
    PATCH  /api/v1/patients/{id}/   — update
    DELETE /api/v1/patients/{id}/   — soft deactivate (sets is_active=False)
    """
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'phone_number', 'location']
    ordering_fields = ['created_at', 'last_name', 'first_name']

    def get_queryset(self):
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return Patient.objects.select_related('health_worker').all()
        return Patient.objects.select_related('health_worker').filter(health_worker=user)

    def get_permissions(self):
        if self.action in ['retrieve', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsPatientOwner()]
        return [IsAuthenticated(), IsHealthWorker()]

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return PatientWriteSerializer
        return PatientSerializer

    def create(self, request, *args, **kwargs):
        serializer = PatientWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = serializer.save(health_worker=request.user)
        logger.info('Patient %s created by %s', patient.id, request.user.email)
        return Response(PatientSerializer(patient).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = PatientWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()
        logger.info('Patient %s updated by %s', patient.id, request.user.email)
        return Response(PatientSerializer(patient).data)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        logger.info('Patient %s deactivated by %s', instance.id, self.request.user.email)

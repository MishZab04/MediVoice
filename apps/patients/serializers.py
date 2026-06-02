from rest_framework import serializers
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    """Read serializer — full patient detail including computed and relational fields."""
    full_name = serializers.ReadOnlyField()
    health_worker_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'sex', 'phone_number', 'location',
            'language_preference', 'is_active',
            'health_worker', 'health_worker_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'health_worker', 'created_at', 'updated_at']

    def get_health_worker_name(self, obj):
        return obj.health_worker.get_full_name()


class PatientWriteSerializer(serializers.ModelSerializer):
    """Write serializer — used for create and update. health_worker is set from the request."""

    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'sex',
            'phone_number', 'location', 'language_preference', 'is_active',
        ]

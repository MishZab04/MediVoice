from rest_framework import serializers
from apps.patients.serializers import PatientSerializer
from .models import AssessmentSession, AssessmentResponse


class StartAssessmentSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField()
    language = serializers.ChoiceField(choices=['en', 'fr', 'pcm'])


class RespondSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    answer_text = serializers.CharField()


class AssessmentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentResponse
        fields = ['question_key', 'question_text', 'answer_text', 'extracted_value', 'created_at']


class AssessmentSessionSerializer(serializers.ModelSerializer):
    responses = AssessmentResponseSerializer(many=True, read_only=True)
    patient = PatientSerializer(read_only=True)

    class Meta:
        model = AssessmentSession
        fields = [
            'id', 'patient', 'health_worker',
            'language', 'current_question', 'status',
            'assessment_priority', 'assessment_report',
            'started_at', 'completed_at', 'responses',
        ]

from rest_framework import serializers
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
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentSession
        fields = [
            'id', 'patient', 'patient_name', 'health_worker',
            'language', 'current_question', 'status',
            'assessment_priority', 'assessment_report',
            'started_at', 'completed_at', 'responses',
        ]

    def get_patient_name(self, obj):
        return obj.patient.full_name

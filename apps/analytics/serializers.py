from rest_framework import serializers


class LanguageBreakdownSerializer(serializers.Serializer):
    en = serializers.IntegerField()
    fr = serializers.IntegerField()
    pcm = serializers.IntegerField()


class StatusBreakdownSerializer(serializers.Serializer):
    completed = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    abandoned = serializers.IntegerField()


class TopWorkerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    email = serializers.EmailField()
    facility_name = serializers.CharField()
    assessment_count = serializers.IntegerField()


class DailyCountSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField()


class SummarySerializer(serializers.Serializer):
    total_assessments = serializers.IntegerField()
    total_patients = serializers.IntegerField()
    total_urgent = serializers.IntegerField()
    completed_this_week = serializers.IntegerField()
    by_language = LanguageBreakdownSerializer()
    by_status = StatusBreakdownSerializer()
    # Admin-only fields — None for health workers
    total_health_workers = serializers.IntegerField(allow_null=True)
    pending_approvals = serializers.IntegerField(allow_null=True)
    top_health_workers = TopWorkerSerializer(many=True, allow_null=True)

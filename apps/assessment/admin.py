from django.contrib import admin
from .models import AssessmentSession, AssessmentResponse


class AssessmentResponseInline(admin.TabularInline):
    model = AssessmentResponse
    extra = 0
    readonly_fields = ['question_key', 'answer_text', 'extracted_value', 'created_at']


@admin.register(AssessmentSession)
class AssessmentSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'health_worker', 'language', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'language']
    search_fields = ['patient__first_name', 'patient__last_name', 'health_worker__email']
    ordering = ['-started_at']
    readonly_fields = ['id', 'started_at', 'completed_at']
    inlines = [AssessmentResponseInline]


@admin.register(AssessmentResponse)
class AssessmentResponseAdmin(admin.ModelAdmin):
    list_display = ['session', 'question_key', 'answer_text', 'created_at']
    list_filter = ['question_key']
    readonly_fields = ['created_at']

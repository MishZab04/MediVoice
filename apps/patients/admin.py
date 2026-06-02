from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'sex', 'language_preference',
        'location', 'health_worker', 'is_active', 'created_at',
    ]
    list_filter = ['sex', 'language_preference', 'is_active']
    search_fields = ['first_name', 'last_name', 'phone_number', 'location']
    ordering = ['-created_at']
    raw_id_fields = ['health_worker']
    readonly_fields = ['id', 'created_at', 'updated_at']

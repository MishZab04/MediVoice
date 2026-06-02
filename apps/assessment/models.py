import uuid
from django.conf import settings
from django.db import models

from apps.patients.models import Patient


class AssessmentStatus(models.TextChoices):
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    ABANDONED = 'abandoned', 'Abandoned'


class AssessmentSession(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'French'),
        ('pcm', 'Pidgin English'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='sessions',
    )
    health_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assessment_sessions',
    )
    language = models.CharField(max_length=3, choices=LANGUAGE_CHOICES)
    current_question = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=AssessmentStatus.choices,
        default=AssessmentStatus.IN_PROGRESS,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Assessment Session'
        verbose_name_plural = 'Assessment Sessions'

    def __str__(self):
        return f"Session {self.id} — {self.patient} ({self.language})"


class AssessmentResponse(models.Model):
    session = models.ForeignKey(
        AssessmentSession,
        on_delete=models.CASCADE,
        related_name='responses',
    )
    question_key = models.CharField(max_length=50)
    answer_text = models.TextField()
    extracted_value = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Assessment Response'
        verbose_name_plural = 'Assessment Responses'
        unique_together = [('session', 'question_key')]

    def __str__(self):
        return f"{self.session_id} — {self.question_key}"

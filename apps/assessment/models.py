import uuid
from django.conf import settings
from django.db import models

from apps.patients.models import Patient


class AssessmentStatus(models.TextChoices):
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    ABANDONED = 'abandoned', 'Abandoned'


class AssessmentPriority(models.TextChoices):
    NORMAL = 'NORMAL', 'Normal'
    URGENT = 'URGENT', 'Urgent'


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
    # Stores the current AI-generated question text (no longer a fixed key)
    current_question = models.TextField(default='')
    status = models.CharField(
        max_length=20,
        choices=AssessmentStatus.choices,
        default=AssessmentStatus.IN_PROGRESS,
    )
    # Full Claude messages array — persisted between API calls
    conversation_history = models.JSONField(default=list)
    # Filled when status becomes COMPLETED
    assessment_report = models.TextField(blank=True, default='')
    assessment_priority = models.CharField(
        max_length=10,
        choices=AssessmentPriority.choices,
        default=AssessmentPriority.NORMAL,
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
    # Sequential identifier: turn_0, turn_1, … — unique per session
    question_key = models.CharField(max_length=50)
    # Full AI-generated question text asked at this turn
    question_text = models.TextField(default='')
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

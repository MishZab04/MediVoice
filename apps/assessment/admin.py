from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html, mark_safe

from .models import AssessmentSession, AssessmentResponse


# ── Custom symptom filter ──────────────────────────────────────────────────────

class SymptomFilter(admin.SimpleListFilter):
    title = 'Symptom'
    parameter_name = 'symptom'

    # Each entry: (url_value, display_label)
    _SYMPTOMS = [
        ('headache',     'Headache'),
        ('fever',        'Fever / Temperature'),
        ('dizziness',    'Dizziness'),
        ('stomach_pain', 'Stomach Pain'),
        ('chest_pain',   'Chest Pain'),
        ('vomiting',     'Vomiting / Nausea'),
        ('weakness',     'Weakness / Fatigue'),
        ('body_pain',    'Body / Muscle Pain'),
        ('appetite',     'Appetite / Eating'),
        ('cough',        'Cough / Breathing'),
    ]

    # Keywords per symptom covering English, French, and Pidgin variants
    _KEYWORDS = {
        'headache':     ['headache', 'head pain', 'mal à la tête', 'tête', 'head dey pain', 'head pain'],
        'fever':        ['fever', 'fièvre', 'temperature', 'température', 'body dey hot', '38', '39', '40'],
        'dizziness':    ['dizz', 'vertige', 'lightheaded', 'head dey turn', 'tourne'],
        'stomach_pain': ['stomach', 'belly', 'abdomen', 'ventre', 'belle', 'abdominal', 'gastric'],
        'chest_pain':   ['chest', 'thoracique', 'poitrine', 'heart', 'cardiac', 'chest pain'],
        'vomiting':     ['vomit', 'nausea', 'nausée', 'throwing up', 'dey vomit', 'vomissement'],
        'weakness':     ['weak', 'faible', 'fatigue', 'tired', 'dey weak', 'weakness', 'faiblesse'],
        'body_pain':    ['body pain', 'muscle', 'douleur', 'aches', 'body dey pain', 'musculaire'],
        'appetite':     ['appetite', 'appétit', 'eating', 'food', 'hunger', 'chop', 'manger'],
        'cough':        ['cough', 'toux', 'breath', 'respir', 'wheez'],
    }

    def lookups(self, request, model_admin):
        return self._SYMPTOMS

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        keywords = self._KEYWORDS.get(self.value(), [self.value()])
        q = Q()
        for kw in keywords:
            q |= Q(question_text__icontains=kw) | Q(answer_text__icontains=kw)
        return queryset.filter(q)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _priority_badge(priority):
    if not priority:
        return mark_safe('<span style="background:#6c757d;color:white;padding:2px 10px;border-radius:12px;font-size:12px">—</span>')
    if priority == 'URGENT':
        return mark_safe('<span style="background:#dc3545;color:white;padding:2px 10px;border-radius:12px;font-size:12px">URGENT</span>')
    return mark_safe('<span style="background:#28a745;color:white;padding:2px 10px;border-radius:12px;font-size:12px">NORMAL</span>')


def _status_badge(status):
    colours = {
        'in_progress': ('#007bff', 'IN PROGRESS'),
        'completed':   ('#28a745', 'COMPLETED'),
        'abandoned':   ('#6c757d', 'ABANDONED'),
    }
    colour, label = colours.get(status, ('#6c757d', status.upper()))
    return format_html(
        '<span style="background:{};color:white;padding:2px 10px;border-radius:12px;font-size:12px">{}</span>',
        colour, label,
    )


# ── Inlines ────────────────────────────────────────────────────────────────────

class AssessmentResponseInline(admin.TabularInline):
    model = AssessmentResponse
    extra = 0
    readonly_fields = ['question_key', 'question_text', 'answer_text', 'extracted_value', 'created_at']


# ── Session admin ──────────────────────────────────────────────────────────────

@admin.register(AssessmentSession)
class AssessmentSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'patient', 'language', 'status_badge',
        'priority_badge', 'started_at', 'completed_at',
    ]
    list_filter = ['status', 'language', 'assessment_priority']
    search_fields = ['patient__first_name', 'patient__last_name', 'health_worker__email']
    ordering = ['-started_at']
    readonly_fields = ['id', 'started_at', 'completed_at', 'conversation_history', 'assessment_report']
    inlines = [AssessmentResponseInline]

    @admin.display(description='Status')
    def status_badge(self, obj):
        return _status_badge(obj.status)

    @admin.display(description='Priority')
    def priority_badge(self, obj):
        if not obj.assessment_priority:
            return mark_safe('<span style="color:#aaa">—</span>')
        return _priority_badge(obj.assessment_priority)


# ── Response admin ─────────────────────────────────────────────────────────────

@admin.register(AssessmentResponse)
class AssessmentResponseAdmin(admin.ModelAdmin):
    list_display = [
        'session_link', 'question_key', 'question_text',
        'answer_text', 'session_priority', 'created_at',
    ]
    list_filter = [SymptomFilter, 'session__language', 'session__assessment_priority']
    search_fields = [
        'question_text', 'answer_text',
        'session__patient__first_name', 'session__patient__last_name',
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    @admin.display(description='Session')
    def session_link(self, obj):
        return format_html(
            '<a href="/admin/assessment/assessmentsession/{}/change/">{} — {}</a>',
            obj.session_id,
            str(obj.session_id)[:8] + '…',
            obj.session.patient.full_name,
        )

    @admin.display(description='Priority')
    def session_priority(self, obj):
        if not obj.session:
            return mark_safe('<span style="color:#aaa">—</span>')
        return _priority_badge(obj.session.assessment_priority)

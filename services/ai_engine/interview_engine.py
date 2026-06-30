import json
import logging

from google import genai
from google.genai import types
from django.conf import settings

logger = logging.getLogger('services')

# ── System prompt ──────────────────────────────────────────────────────────────
# {language} is replaced at runtime with the actual language name.

_SYSTEM_PROMPT_TEMPLATE = """\
You are the AI Clinical Interview Engine for MediVoice, a voice-guided patient assessment system.

Your role is to conduct a natural, conversational medical interview with a patient through voice \
interaction. You are NOT a diagnostic system and must never provide a final diagnosis. Your \
responsibility is to collect accurate clinical information and generate a structured assessment \
report for a healthcare worker.

CORE BEHAVIOR

1. The patient communicates by voice.
2. The patient's speech has already been converted to text using Speech-to-Text (STT).
3. Analyze the patient's response and extract:
   - Main symptoms
   - Duration
   - Severity
   - Associated symptoms
   - Relevant medical history
   - Current medications
   - Allergies
   - Risk factors
4. Determine what clinical information is still missing.
5. Generate ONLY the next best question needed to continue the assessment.
6. The generated question will later be converted to speech using Text-to-Speech (TTS).
7. Continue until sufficient information has been collected.
8. Maintain a natural conversation instead of following a fixed questionnaire.

LANGUAGE RULES

PATIENT_LANGUAGE = {language}

Always:
- Ask questions in {language}.
- Understand patient responses in {language}.
- Keep questions simple, natural, and conversational.
- Never switch languages unless instructed.

ASSESSMENT STRATEGY

After the patient describes their main complaint, dynamically investigate:
- Duration
- Severity
- Frequency
- Location
- Progression
- Associated symptoms
- Aggravating and relieving factors
- Relevant medical history
- Medication use
- Allergies

Do not ask unnecessary questions.
Do not ask multiple unrelated questions at once.
Prioritize clinically important follow-up questions.

RED FLAG DETECTION

Monitor for urgent warning signs such as:
- Difficulty breathing
- Chest pain
- Loss of consciousness
- Severe bleeding
- Stroke symptoms (sudden facial drooping, arm weakness, speech difficulty)
- Seizures
- Suicidal statements
- Severe allergic reactions

If detected: set priority to "URGENT" and ask clarifying safety questions immediately.

CONVERSATION MEMORY

- Never ask for information the patient has already provided.
- Track all symptoms, history, and context from earlier turns.
- For Pidgin English responses, patient speech may contain minor transcription
  errors from speech recognition. Always interpret charitably based on context.
  For example "my eye is torn" means dizziness, "body they hot" means fever.

ASSESSMENT COMPLETION

Stop asking questions and generate the report when you have collected sufficient information across:
- Chief complaint and main symptoms
- Duration and severity
- Associated symptoms
- Relevant medical history or risk factors
- Medications and allergies (even if none reported)

The report must be written in English or French only (never Pidgin), regardless of interview language.

OUTPUT FORMAT — CRITICAL

Every response MUST be a single valid JSON object. No markdown, no prose outside the JSON.

When the interview is still in progress:
{{"status": "in_progress", "question": "<next question in {language}>"}}

When enough information has been collected:
{{"status": "completed", "priority": "NORMAL", "report": "<full structured clinical assessment report in English or French>"}}

Use "URGENT" instead of "NORMAL" when a red flag was detected.

The report must include:
- Patient complaints
- Symptoms collected with duration and severity
- Relevant medical history and risk factors
- Medications and allergies
- Red flags detected (if any)
- Assessment priority (NORMAL / URGENT)
- Statement that the report is for review by a healthcare professional only

Do not provide a diagnosis. Do not prescribe treatment.
"""

# Pure clinical question — used only for the Gemini conversation history seed.
_PURE_OPENING_QUESTIONS = {
    'en':  "Please tell me what brings you here today.",
    'fr':  "Dites-moi ce qui vous amène ici aujourd'hui.",
    'pcm': "Abeg tell me wetin bring you here today.",
}

# Spoken to the patient when the assessment is complete.
_COMPLETION_MESSAGES = {
    'en': {
        'NORMAL': (
            "Thank you very much for answering all the questions. "
            "Your health information has been recorded and a report has been prepared for your healthcare worker. "
            "Please visit a doctor or nurse soon so they can review your case and help you."
        ),
        'URGENT': (
            "Thank you. Your assessment is now complete. "
            "Based on your symptoms, you need urgent medical attention. "
            "Please go to the nearest clinic or hospital immediately. Do not wait."
        ),
    },
    'fr': {
        'NORMAL': (
            "Merci beaucoup d'avoir répondu à toutes les questions. "
            "Vos informations de santé ont été enregistrées et un rapport a été préparé pour votre professionnel de santé. "
            "Veuillez consulter un médecin ou une infirmière prochainement."
        ),
        'URGENT': (
            "Merci. Votre évaluation est maintenant terminée. "
            "En raison de vos symptômes, vous avez besoin d'une attention médicale urgente. "
            "Veuillez vous rendre immédiatement à la clinique ou à l'hôpital le plus proche."
        ),
    },
    'pcm': {
        'NORMAL': (
            "Tank you well well for answering all di questions. "
            "We don record your health information and we don prepare report for your doctor. "
            "Abeg go see doctor or nurse soon make dem check you well."
        ),
        'URGENT': (
            "Tank you. Your assessment don finish. "
            "Based on wetin you tell us, you need to see doctor urgently. "
            "Abeg go nearest clinic or hospital immediately. No waste time."
        ),
    },
}

_LANGUAGE_NAMES = {
    'en':  'English',
    'fr':  'French',
    'pcm': 'Pidgin English',
}

_FALLBACK_QUESTIONS = {
    'en':  "Could you please tell me more about how you are feeling?",
    'fr':  "Pouvez-vous m'en dire plus sur ce que vous ressentez ?",
    'pcm': "Fit you tell me more about wetin dey worry you?",
}


def _part(text: str) -> dict:
    """Build a single Gemini part dict."""
    return {"text": text}


def _msg(role: str, text: str) -> dict:
    """Build a single Gemini content dict for JSON storage."""
    return {"role": role, "parts": [_part(text)]}


class InterviewResult:
    """Holds one turn's result from the AI engine."""

    __slots__ = ('status', 'question', 'priority', 'report')

    def __init__(
        self,
        status: str,
        question: str = '',
        priority: str = 'NORMAL',
        report: str = '',
    ):
        self.status = status      # 'in_progress' | 'completed'
        self.question = question  # next question text  (in_progress)
        self.priority = priority  # 'NORMAL' | 'URGENT' (completed)
        self.report = report      # structured report   (completed)


class InterviewEngine:
    """
    Wraps the Google Gemini API (google-genai SDK) to drive a dynamic
    clinical interview.

    Conversation history is stored in Gemini dict format:
        [
            {"role": "user",  "parts": [{"text": "[Assessment started]"}]},
            {"role": "model", "parts": [{"text": "Please tell me what brings you here today."}]},
            {"role": "user",  "parts": [{"text": "I have had fever for 3 days"}]},
            {"role": "model", "parts": [{"text": "How high is the fever?"}]},
            ...
        ]

    Rules enforced by Gemini:
    - History must START with role "user".
    - Roles must ALTERNATE strictly (user → model → user → …).
    - The current patient answer is appended as the final "user" entry
      and passed as part of `contents` in the API call — it is NOT
      included in the stored history until after the response is received.
    """

    def opening_question(self, language: str, patient_name: str = '') -> InterviewResult:
        """
        Return the personalised opening greeting + question. No API call.
        Greeting is time-aware (morning / afternoon / evening) and in the
        patient's language.
        """
        question = self._build_opening(language, patient_name)
        return InterviewResult(status='in_progress', question=question)

    # ── Opening builder ────────────────────────────────────────────────────────

    @staticmethod
    def _time_greeting(language: str) -> str:
        from django.utils import timezone
        hour = timezone.localtime().hour
        if 5 <= hour < 12:
            period = 'morning'
        elif 12 <= hour < 18:
            period = 'afternoon'
        else:
            period = 'evening'

        _greetings = {
            'en':  {'morning': 'Good morning',  'afternoon': 'Good afternoon',  'evening': 'Good evening'},
            'fr':  {'morning': 'Bonjour',        'afternoon': 'Bon après-midi',  'evening': 'Bonsoir'},
            'pcm': {'morning': 'Good morning',   'afternoon': 'Good afternoon',  'evening': 'Good evening'},
        }
        return _greetings.get(language, _greetings['en'])[period]

    def _build_opening(self, language: str, patient_name: str) -> str:
        greeting = self._time_greeting(language)
        name = f" {patient_name}," if patient_name else ","

        if language == 'fr':
            return (
                f"{greeting}{name} bienvenue sur MediVoice ! "
                "Je suis ici pour recueillir vos informations de santé pour votre professionnel de santé. "
                "Dites-moi ce qui vous amène ici aujourd'hui."
            )
        if language == 'pcm':
            return (
                f"{greeting}{name} welcome to MediVoice! "
                "I dey here to help gather your health information for your doctor. "
                "Abeg tell me wetin bring you here today."
            )
        # English (default)
        return (
            f"{greeting}{name} welcome to MediVoice! "
            "I am here to help collect your health information for your healthcare worker. "
            "Please tell me what brings you here today."
        )

    def initial_history(self, language: str) -> list:
        """
        Seed the conversation history for a new session.
        Uses the pure clinical question (no welcome prefix) so Gemini stays
        focused on the medical interview.
        Gemini requires the first turn to be 'user'.
        """
        pure_question = _PURE_OPENING_QUESTIONS.get(language, _PURE_OPENING_QUESTIONS['en'])
        return [
            _msg("user",  "[Assessment started. Begin the patient interview.]"),
            _msg("model", pure_question),
        ]

    def completion_message(self, language: str, priority: str) -> str:
        """Return the spoken completion message in the patient's language."""
        lang = language if language in _COMPLETION_MESSAGES else 'en'
        p = priority if priority in ('NORMAL', 'URGENT') else 'NORMAL'
        return _COMPLETION_MESSAGES[lang][p]

    def next_turn(
        self,
        conversation_history: list,
        patient_answer: str,
        language: str,
    ) -> InterviewResult:
        """
        Given the stored conversation history and the patient's latest answer,
        call Gemini and return the next question or the completed report.

        conversation_history: messages *before* this answer, in Gemini dict
                              format (role: user/model, parts: [{text: ...}]).
        patient_answer: raw STT text of the patient's current response.
        """
        # Compute which fixed question to serve if the API is unreachable.
        # History layout: [seed_user, opening_model] + [user, model] * N
        # So N = (len - 2) // 2 maps to QUESTION_ORDER index.
        offline_index = max(0, (len(conversation_history) - 2) // 2)

        contents = conversation_history + [_msg("user", patient_answer)]

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model=settings.AI_ENGINE_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self._build_system_prompt(language),
                    response_mime_type="application/json",
                ),
            )
            raw = response.text.strip()
            logger.debug('AI engine raw response (%.120s...)', raw[:120])
            return self._parse(raw, language)

        except Exception as exc:
            logger.warning(
                'Gemini unavailable (offline_index=%s) — falling back to fixed questionnaire: %s',
                offline_index, exc,
            )
            from services.questionnaire.questions import QUESTION_ORDER
            if offline_index >= len(QUESTION_ORDER):
                logger.info('All fixed questions exhausted — generating offline report')
                return self._build_offline_report(conversation_history, patient_answer, language)
            return self._offline_fallback(language, offline_index)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _build_system_prompt(self, language: str) -> str:
        lang_name = _LANGUAGE_NAMES.get(language, 'English')
        return _SYSTEM_PROMPT_TEMPLATE.format(language=lang_name)

    def _parse(self, raw: str, language: str) -> InterviewResult:
        """Parse the JSON response from Gemini. Falls back gracefully if malformed."""
        text = raw
        # Strip markdown code fences the model sometimes adds
        if text.startswith('```'):
            lines = text.splitlines()
            text = '\n'.join(lines[1:])
            if text.endswith('```'):
                text = text[:-3].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning('AI engine: non-JSON response, treating as question')
            return InterviewResult(status='in_progress', question=raw.strip())

        status = data.get('status', 'in_progress')

        if status == 'completed':
            return InterviewResult(
                status='completed',
                priority=data.get('priority', 'NORMAL'),
                report=data.get('report', ''),
            )

        question = data.get('question', '').strip()
        if not question:
            logger.warning('AI engine: empty question in response')
            return InterviewResult(
                status='in_progress',
                question=_FALLBACK_QUESTIONS.get(language, _FALLBACK_QUESTIONS['en']),
            )

        return InterviewResult(status='in_progress', question=question)

    def _build_offline_report(
        self,
        conversation_history: list,
        patient_answer: str,
        language: str,
    ) -> InterviewResult:
        """
        Build a structured narrative report from the Q&A history when Gemini is
        unavailable and all 10 fixed questions have been answered.
        History layout: [seed_user, opening_model, user, model, user, model, ...]
        Questions are at odd indices (1,3,5…), answers at even indices (2,4,6…).
        """
        pairs = []
        for i in range(1, len(conversation_history) - 1, 2):
            q_msg = conversation_history[i]
            a_msg = conversation_history[i + 1] if i + 1 < len(conversation_history) else None
            if q_msg.get('role') == 'model' and a_msg and a_msg.get('role') == 'user':
                q = q_msg['parts'][0]['text']
                a = a_msg['parts'][0]['text']
                if not q.startswith('[Assessment'):
                    pairs.append((q, a))

        # Add the current unanswered question + patient's final answer
        if conversation_history and conversation_history[-1].get('role') == 'model':
            last_q = conversation_history[-1]['parts'][0]['text']
            if not last_q.startswith('[Assessment'):
                pairs.append((last_q, patient_answer))

        report = self._build_narrative_from_pairs(pairs, language)
        return InterviewResult(status='completed', priority='NORMAL', report=report)

    def _build_narrative_from_pairs(self, pairs: list, language: str) -> str:
        """Convert Q&A pairs into a structured clinical narrative report."""
        from services.questionnaire.questions import QUESTIONS

        # Build reverse lookup across all languages so Pidgin questions map to keys too
        all_q_to_key: dict[str, str] = {}
        for lang_qs in QUESTIONS.values():
            for key, text in lang_qs.items():
                all_q_to_key[text.strip().lower()] = key

        chief_complaint = None
        findings: dict[str, str] = {}

        for q, a in pairs:
            key = all_q_to_key.get(q.strip().lower())
            if key is None:
                if chief_complaint is None:
                    chief_complaint = a.strip()
            else:
                findings[key] = a.strip()

        use_french = (language == 'fr')
        lines: list[str] = []

        if use_french:
            lines.append("Plaintes du patient:")
            if chief_complaint:
                lines.append(f"Le patient présente : {chief_complaint}")
            if 'duration' in findings:
                lines.append(f"Durée des symptômes : {findings['duration']}")

            lines.append("")
            lines.append("Symptômes:")
            for key, label in [
                ('fever',         'Fièvre'),
                ('vomiting',      'Vomissements'),
                ('body_weakness', 'Faiblesse corporelle'),
                ('headache',      'Céphalées'),
                ('dizziness',     'Vertiges'),
                ('body_pain',     'Douleurs corporelles'),
                ('appetite',      'Appétit'),
            ]:
                if key in findings:
                    lines.append(f"- {label}: {findings[key]}")
            if 'stomach_pain' in findings:
                detail = findings['stomach_pain']
                if 'pain_description' in findings:
                    detail += f". {findings['pain_description']}"
                lines.append(f"- Douleur abdominale: {detail}")

            lines.append("")
            lines.append("Antécédents médicaux:")
            lines.append(
                "Aucun antécédent médical n'a été collecté lors de cette session hors ligne. "
                "Le professionnel de santé devra compléter cet historique lors de la consultation."
            )

            lines.append("")
            lines.append("Médicaments:")
            lines.append(
                "Aucune information sur les médicaments n'a été collectée lors de cette session hors ligne."
            )

            lines.append("")
            lines.append("Allergies:")
            lines.append(
                "Aucune information sur les allergies n'a été collectée lors de cette session hors ligne."
            )

            lines.append("")
            lines.append("Priorité d'évaluation:")
            lines.append(
                "NORMAL — Ce rapport a été généré à partir d'un questionnaire hors ligne en raison d'une "
                "indisponibilité de la connexion IA. Un professionnel de santé doit examiner les réponses "
                "et déterminer la priorité clinique appropriée."
            )

            lines.append("")
            lines.append(
                "Note: Ce rapport a été généré en mode hors ligne (connexion IA indisponible). "
                "Pour un bilan IA complet, assurez-vous d'avoir une connexion internet lors de la prochaine session. "
                "Ce document est destiné à la révision par un professionnel de santé uniquement."
            )

        else:
            # English — also used for Pidgin sessions
            lines.append("Patient Complaints:")
            if chief_complaint:
                lines.append(f"Patient presents with: {chief_complaint}")
            if 'duration' in findings:
                lines.append(f"Duration of symptoms: {findings['duration']}")

            lines.append("")
            lines.append("Symptoms:")
            for key, label in [
                ('fever',         'Fever'),
                ('vomiting',      'Vomiting'),
                ('body_weakness', 'Body weakness'),
                ('headache',      'Headache'),
                ('dizziness',     'Dizziness'),
                ('body_pain',     'Body pain'),
                ('appetite',      'Appetite'),
            ]:
                if key in findings:
                    lines.append(f"- {label}: {findings[key]}")
            if 'stomach_pain' in findings:
                detail = findings['stomach_pain']
                if 'pain_description' in findings:
                    detail += f". {findings['pain_description']}"
                lines.append(f"- Stomach pain: {detail}")

            lines.append("")
            lines.append("Relevant Medical History and Risk Factors:")
            lines.append(
                "No medical history was collected during this offline assessment session. "
                "The healthcare professional should obtain a full history during the consultation."
            )

            lines.append("")
            lines.append("Medications:")
            lines.append(
                "No medication information was collected during this offline assessment session."
            )

            lines.append("")
            lines.append("Allergies:")
            lines.append(
                "No allergy information was collected during this offline assessment session."
            )

            lines.append("")
            lines.append("Assessment Priority:")
            lines.append(
                "NORMAL — This report was generated from an offline questionnaire due to unavailable "
                "AI connectivity. A healthcare professional should review the patient responses and "
                "determine appropriate clinical priority."
            )

            lines.append("")
            lines.append(
                "Note: This report was generated in offline mode (AI connection unavailable). "
                "For a comprehensive AI-generated assessment, ensure internet connectivity for the next session. "
                "This document is intended for review by a healthcare professional only."
            )

        return "\n".join(lines)

    def _offline_fallback(self, language: str, turn_index: int) -> InterviewResult:
        """
        Fall back to the fixed 10-question set when Gemini is unreachable.
        turn_index maps directly to QUESTION_ORDER so patients still get a
        sensible, clinically ordered sequence instead of a repeated generic prompt.
        """
        from services.questionnaire.questions import QUESTIONS, QUESTION_ORDER
        lang = language if language in QUESTIONS else 'en'
        if turn_index < len(QUESTION_ORDER):
            key = QUESTION_ORDER[turn_index]
            question = QUESTIONS[lang][key]
            logger.info('Offline fallback: question "%s" (index %s)', key, turn_index)
        else:
            question = _FALLBACK_QUESTIONS.get(language, _FALLBACK_QUESTIONS['en'])
        return InterviewResult(status='in_progress', question=question)

import logging
import os

from django.conf import settings

from services.questionnaire.questions import QUESTIONS
from .english_tts import EnglishTTSService
from .french_tts import FrenchTTSService
from .pidgin_tts import PidginTTSService

logger = logging.getLogger('services')

TTS_DIR = os.path.join(settings.MEDIA_ROOT, 'tts')

_SERVICES = {
    'en': EnglishTTSService(),
    'fr': FrenchTTSService(),
    'pcm': PidginTTSService(),
}


def _audio_filename(language: str, question_key: str) -> str:
    return f"{language}_{question_key}.mp3"


def get_audio_url(question_key: str, language: str) -> str | None:
    """Return the media URL for a pre-generated question audio file, or None if missing."""
    filename = _audio_filename(language, question_key)
    filepath = os.path.join(TTS_DIR, filename)
    if os.path.exists(filepath):
        return f"{settings.MEDIA_URL}tts/{filename}"
    logger.warning('TTS file missing: %s — run generate_question_audio', filename)
    return None


def generate_dynamic_audio(
    text: str,
    language: str,
    session_id: str,
    turn: int,
) -> str | None:
    """
    Generate a TTS audio file on demand for an AI-generated question.

    Files are stored as:  media/tts/dynamic_{session_id}_{turn}.mp3
    Returns the MEDIA_URL path, or None on failure.
    """
    os.makedirs(TTS_DIR, exist_ok=True)
    filename = f"dynamic_{session_id}_{turn}.mp3"
    filepath = os.path.join(TTS_DIR, filename)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return f"{settings.MEDIA_URL}tts/{filename}"

    service = _SERVICES.get(language, _SERVICES['en'])
    try:
        service.generate(text=text, output_path=filepath)
        return f"{settings.MEDIA_URL}tts/{filename}"
    except Exception as exc:
        logger.error('Dynamic TTS failed for session %s turn %s: %s', session_id, turn, exc)
        return None


def generate_all_question_audio() -> dict[str, str]:
    """
    Pre-generate MP3 files for all 30 question/language combinations.
    Returns a dict of {key: 'ok' | 'error: <message>'}.
    Safe to re-run — skips files that already exist.
    """
    os.makedirs(TTS_DIR, exist_ok=True)
    results = {}

    for language, questions in QUESTIONS.items():
        service = _SERVICES[language]
        for question_key, text in questions.items():
            filename = _audio_filename(language, question_key)
            filepath = os.path.join(TTS_DIR, filename)
            label = f"{language}_{question_key}"

            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                results[label] = 'skipped (already exists)'
                continue

            try:
                service.generate(text=text, output_path=filepath)
                results[label] = 'ok'
                logger.info('Generated TTS: %s', filename)
            except Exception as exc:
                results[label] = f'error: {exc}'
                logger.error('TTS generation failed for %s: %s', filename, exc)

    return results

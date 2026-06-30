import logging
import os
import threading

import whisper

# Ensure ffmpeg is findable regardless of which shell started the server.
_FFMPEG_BIN = r"C:\ffmpeg\ffmpeg-8.1.1-essentials_build\bin"
if os.path.isdir(_FFMPEG_BIN) and _FFMPEG_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _FFMPEG_BIN + os.pathsep + os.environ["PATH"]

logger = logging.getLogger('services')

_WHISPER_LANGUAGES = {
    'en':  'en',
    'fr':  'fr',
    'pcm': 'en',  # Pidgin → transcribe as English (closest supported model)
}

# Initial prompts guide the acoustic model before transcription starts.
# For Pidgin, this reduces mis-transcription of common vocabulary.
_INITIAL_PROMPTS = {
    'en': None,
    'fr': None,
    'pcm': (
        "Pidgin English from Cameroon. Medical interview. "
        "Common words: dey (is/are/doing), don (have/has/already), di (is/doing), "
        "na (it is/that is), belle (stomach/belly), abeg (please), fit (can), "
        "body dey hot (fever), head dey turn (dizzy), belle dey pain (stomach pain), "
        "body dey pain (body aches), dey vomit (vomiting), I don vomit (I vomited), "
        "no get (don't have), e dey (it is), I don (I have already), "
        "two times (twice), four days (four days)."
    ),
}

_model = None
_model_lock = threading.Lock()


def _get_model() -> whisper.Whisper:
    """Load the openai-whisper base model once and reuse it (lazy singleton)."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info('Loading Whisper small model...')
                _model = whisper.load_model('small')
                logger.info('Whisper model loaded.')
    return _model


def transcribe(audio_path: str, language: str = 'en') -> str:
    """
    Transcribe an audio file to text using openai-whisper.

    audio_path: absolute path to the audio file (.wav, .mp3, .m4a, .webm, etc.)
    language:   session language code ('en', 'fr', 'pcm')
    Returns:    transcribed text string
    """
    whisper_lang = _WHISPER_LANGUAGES.get(language, 'en')
    model = _get_model()

    logger.info('Transcribing %s (language=%s)', os.path.basename(audio_path), whisper_lang)

    prompt = _INITIAL_PROMPTS.get(language)
    result = model.transcribe(
        audio_path,
        language=whisper_lang,
        initial_prompt=prompt,
        temperature=0,            # deterministic output, reduces hallucination
        no_speech_threshold=0.6,  # skip silent/non-speech segments
        logprob_threshold=-1.0,   # filter low-confidence segments
        condition_on_previous_text=False,
    )

    text = result['text'].strip()

    if language == 'pcm':
        from services.normalization.pidgin import normalize
        text = normalize(text)
        logger.info('Normalized Pidgin: %s', text[:120])
    else:
        logger.info('Transcription result: %s', text[:120])

    return text

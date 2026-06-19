from django.apps import AppConfig


class VoiceProcessingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.voice_processing'
    label = 'voice_processing'

    def ready(self):
        # Pre-load the Whisper model at startup so the first transcription
        # request doesn't block for 30-60 seconds.
        import threading
        def _preload():
            try:
                from services.stt.whisper_stt import _get_model
                _get_model()
            except Exception:
                pass
        threading.Thread(target=_preload, daemon=True).start()

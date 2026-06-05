import logging
import os
import tempfile

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsHealthWorker
from services.stt.whisper_stt import transcribe

logger = logging.getLogger('apps.voice_processing')


class TranscribeView(APIView):
    """
    POST /api/v1/voice/transcribe/
    Upload an audio file and receive the transcribed text.
    Supports .wav, .mp3, .m4a, .webm, .ogg.
    """
    permission_classes = [IsAuthenticated, IsHealthWorker]
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=inline_serializer('TranscribeRequest', fields={
            'audio': drf_serializers.FileField(),
            'language': drf_serializers.ChoiceField(choices=['en', 'fr', 'pcm'], default='en'),
        }),
        responses={
            200: inline_serializer('TranscribeResponse', fields={
                'text': drf_serializers.CharField(),
                'language': drf_serializers.CharField(),
            }),
        },
        summary='Transcribe patient voice to text',
        description=(
            'Accepts an audio file recorded by the patient and returns the '
            'transcribed text using Whisper. Pass the returned text as '
            'answer_text in POST /api/v1/assessment/respond/.'
        ),
    )
    def post(self, request):
        audio_file = request.FILES.get('audio')
        language = request.data.get('language', 'en')

        if not audio_file:
            return Response(
                {'detail': 'No audio file provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save upload to a temp file so Whisper can read it
        suffix = os.path.splitext(audio_file.name)[-1] or '.wav'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in audio_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            text = transcribe(audio_path=tmp_path, language=language)
            logger.info('Transcribed audio for user %s: %s', request.user.email, text[:80])
            return Response({'text': text, 'language': language})
        except Exception as exc:
            logger.error('Transcription failed: %s', exc)
            return Response(
                {'detail': f'Transcription failed: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            os.unlink(tmp_path)

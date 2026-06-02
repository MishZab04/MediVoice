import asyncio
import edge_tts
from .base import BaseTTSService

VOICE = 'en-NG-EzinneNeural'


class PidginTTSService(BaseTTSService):
    """
    Pidgin English TTS using Microsoft Edge TTS with Nigerian English voice
    (en-NG-EzinneNeural). Uses SSML prosody to force rising intonation so
    questions sound like questions, not statements.
    """
    def generate(self, text: str, output_path: str) -> None:
        asyncio.run(self._generate_async(text, output_path))

    async def _generate_async(self, text: str, output_path: str) -> None:
        communicate = edge_tts.Communicate(text, VOICE, rate='-15%', pitch='+25Hz')
        await communicate.save(output_path)

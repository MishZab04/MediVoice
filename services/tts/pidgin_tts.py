import asyncio
import edge_tts
from .base import BaseTTSService

VOICE = 'en-NG-AbeoNeural'


class PidginTTSService(BaseTTSService):
    """
    Pidgin English TTS using Microsoft Edge TTS with Nigerian English male voice
    (en-NG-AbeoNeural). Slightly slower rate for clarity.
    """
    def generate(self, text: str, output_path: str) -> None:
        asyncio.run(self._generate_async(text, output_path))

    async def _generate_async(self, text: str, output_path: str) -> None:
        communicate = edge_tts.Communicate(text, VOICE, rate='-10%')
        await communicate.save(output_path)

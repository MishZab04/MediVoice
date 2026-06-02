import asyncio
import edge_tts
from .base import BaseTTSService

VOICE = 'en-US-JennyNeural'


class EnglishTTSService(BaseTTSService):
    def generate(self, text: str, output_path: str) -> None:
        asyncio.run(self._generate_async(text, output_path))

    async def _generate_async(self, text: str, output_path: str) -> None:
        communicate = edge_tts.Communicate(text, VOICE, rate='-5%')
        await communicate.save(output_path)

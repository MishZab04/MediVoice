from gtts import gTTS
from .base import BaseTTSService


class FrenchTTSService(BaseTTSService):
    def generate(self, text: str, output_path: str) -> None:
        tts = gTTS(text=text, lang='fr', slow=False)
        tts.save(output_path)

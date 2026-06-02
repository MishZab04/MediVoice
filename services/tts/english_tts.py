from gtts import gTTS
from .base import BaseTTSService


class EnglishTTSService(BaseTTSService):
    def generate(self, text: str, output_path: str) -> None:
        tts = gTTS(text=text, lang='en', tld='com', slow=False)
        tts.save(output_path)

from abc import ABC, abstractmethod


class BaseTTSService(ABC):
    @abstractmethod
    def generate(self, text: str, output_path: str) -> None:
        """Convert text to speech and save MP3 to output_path."""
        pass

import asyncio
import math
import uuid

from mutagen.mp3 import MP3
from openai import OpenAI

from config import ROUTERAI_API_KEY, ROUTERAI_BASE_URL, ROOT


MODEL = "x-ai/grok-voice-tts-1.0"
VOICE = "leo"


def _unique_filename(prefix: str, suffix: str) -> str:
    while True:
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}{suffix}"
        if not (ROOT / filename).exists():
            return filename


def _generate_speech_file(text: str) -> tuple[str, str]:
    client = OpenAI(api_key=ROUTERAI_API_KEY, base_url=ROUTERAI_BASE_URL)

    filename = _unique_filename("output", ".mp3")
    file_path = ROOT / filename

    response = client.audio.speech.create(
        model=MODEL,
        voice=VOICE,
        input=text,
        response_format="mp3",
    )
    response.stream_to_file(str(file_path))

    audio = MP3(file_path)
    duration = math.ceil(audio.info.length * 1000) / 1000
    return str(file_path), str(duration)


async def generate_text(text: str) -> tuple[str, str]:
    return await asyncio.to_thread(_generate_speech_file, text)


if __name__ == "__main__":
    test_text = "Привет! Это пример синтеза речи через RouterAI."
    file_path, dur = asyncio.run(generate_text(test_text))
    print(f"Файл: {file_path}\nДлительность: {dur} сек.")

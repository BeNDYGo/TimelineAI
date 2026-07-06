import asyncio
import math
import subprocess
import uuid

from openai import OpenAI

from config import ROUTERAI_API_KEY, ROUTERAI_BASE_URL, VODS


MODEL = "x-ai/grok-voice-tts-1.0"
VOICE = "leo"


def _unique_filename(prefix: str, suffix: str) -> str:
    while True:
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}{suffix}"
        if not (VODS / filename).exists():
            return filename


def _get_duration(file_path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr[:500]}")
    return math.ceil(float(result.stdout.strip()) * 1000) / 1000


def _generate_speech_file(text: str) -> tuple[str, str]:
    client = OpenAI(api_key=ROUTERAI_API_KEY, base_url=ROUTERAI_BASE_URL)

    filename = _unique_filename("output", ".mp3")
    VODS.mkdir(exist_ok=True)
    file_path = VODS / filename

    response = client.audio.speech.create(
        model=MODEL,
        voice=VOICE,
        input=text,
        response_format="mp3",
    )
    response.stream_to_file(str(file_path))

    duration = _get_duration(file_path)
    return filename, str(duration)


async def generate_text(text: str) -> tuple[str, str]:
    return await asyncio.to_thread(_generate_speech_file, text)


if __name__ == "__main__":
    test_text = "Привет! Это пример синтеза речи через RouterAI."
    file_path, dur = asyncio.run(generate_text(test_text))
    print(f"Файл: {file_path}\nДлительность: {dur} сек.")

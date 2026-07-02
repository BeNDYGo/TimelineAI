import asyncio
import edge_tts
import uuid
import os
import math
from mutagen.mp3 import MP3

async def generate_text_edge(text: str, voice: str) -> tuple[str, str]:
    if voice == "w": 
        voice_id = "ru-RU-SvetlanaNeural"
    else: 
        voice_id = "ru-RU-DmitryNeural"

    filename = f"output_{uuid.uuid4().hex}.mp3"
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(filename)
    
    filepath = os.path.abspath(filename)
    audio = MP3(filepath)
    duration = audio.info.length
    duration_formatted = f"{math.ceil(duration * 1000) / 1000}"
    return filepath, duration_formatted

if __name__ == "__main__":
    test_text = "Я установил библиотеку edge-tts для Python. It works perfectly! Надеюсь, этот баг пофиксят."
    
    file_path, dur = asyncio.run(generate_text_edge(test_text, "m"))
    print(f"Файл: {file_path}\nДлительность: {dur} сек.")
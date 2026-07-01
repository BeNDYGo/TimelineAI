import sys
import os
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from TTS import generateText
from TTI import generate
from video.assembler import save_scene as _save_scene, assemble_video as _assemble_video, clear_manifest


mcp = FastMCP("timeline-tools")


@mcp.tool()
def generate_speech(voice_style: str, lang: str, text: str) -> dict:
    """
    Превращает текст в аудиофайл
    
    Args:
        voice_style: Стиль голоса. Доступны женские (F1, F2, F3, F4, F5) и мужские (M1, M2, M3, M4, M5).
        lang: Код языка в формате ISO (например, 'ru', 'en').
        text: Текст который будет озвучен
    Returns:
        путь к файлу и длительность в json формате
    """
    filename, duration = generateText(voice_style, lang, text)
    return {"filename": filename, "duration": duration}


@mcp.tool()
def generate_image(prompt: str, image: str = None, aspect_ratio: str = "auto") -> dict:
    """Сгенерировать кадр по текстовому описанию
    
    Args:
        prompt: Текстовое описание изображения
        image: Имя файла референс-изображения в корне проекта (опционально)
        aspect_ratio: Соотношение сторон изображения. Доступные значения: 16:9, 9:16, 1:1, auto.
                   Если по контексту не понятно - укажите auto.
    
    Returns:
        Имя сгенерированного файла
    """
    return {"filename": generate(prompt, image=image, aspect_ratio=aspect_ratio)}


@mcp.tool()
def save_scene(scene_number: int, image: str, audio: str, duration: float) -> dict:
    """Сохранить сцену в манифест для последующей склейки видео

    Args:
        scene_number: Номер сцены (начиная с 1)
        image: Имя файла изображения (сгенерированного через generate_image)
        audio: Имя файла аудио (сгенерированного через generate_speech)
        duration: Длительность аудио в секундах
    Returns:
        Статус сохранения и количество сцен в манифесте
    """
    return _save_scene(scene_number, image, audio, duration)


@mcp.tool()
def assemble_video() -> dict:
    """Склеить все сцены из манифеста в один видеофайл final.mp4.
    Вызывай этот инструмент ПОСЛЕ того как все сцены сохранены через save_scene.
    Не принимает параметров — читает манифест автоматически.

    Returns:
        Результат сборки: путь к файлу и количество сцен
    """
    return _assemble_video()


if __name__ == "__main__":
    mcp.run()

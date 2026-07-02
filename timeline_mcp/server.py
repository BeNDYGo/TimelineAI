import sys
import os
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from TTS import generate_text_edge
from TTI import generate
from video.assembler import save_scene as _save_scene, assemble_video as _assemble_video, clear_manifest


mcp = FastMCP("timeline-tools")


@mcp.tool()
async def generate_speech(text: str, gender: str = "m") -> dict:
    """
    Превращает текст в аудиофайл

    Args:
        text: Текст который будет озвучен
        gender: Пол спикера: "m" — мужской, "w" — женский
    Returns:
        путь к файлу и длительность в json формате
    """
    filename, duration = await generate_text_edge(text, gender)
    return {"filename": os.path.basename(filename), "duration": duration}


@mcp.tool()
def generate_image(prompt: str) -> dict:
    """Сгенерировать кадр по текстовому описанию
    
    Args:
        prompt: Текстовое описание изображения
    
    Returns:
        Имя сгенерированного файла
    """
    return {"filename": generate(prompt, aspect_ratio="auto")}


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

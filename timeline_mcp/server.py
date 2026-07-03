import sys
import os
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from TTS import generate_text_edge
from TTI import generate
from video.assembler import save_scene as _save_scene, assemble_video as _assemble_video, clear_manifest

# Import the agent functions
from agent1_producer import run as producer_run
from agent2_screenwriter import run as screenwriter_run
from agent3_director import run as director_run

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
    return {"filename": generate(prompt, aspect_ratio="9:16")}


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


@mcp.tool()
async def create_video_from_topic(topic: str, voice: str = "m") -> dict:
    """
    Полный цикл создания видео: тема -> бриф -> сценарий -> аудио/изображения -> итоговое видео.

    Args:
        topic: Тема будущего видео.
        voice: Пол спикера: "m" — мужской, "w" — женский (по умолчанию "m").

    Returns:
        Словарь с именем файла и статусом.
    """
    try:
        # Шаг 1: Продюссер — тема → бриф
        brief = await producer_run(topic)
        # Шаг 2: Сценарист — бриф → текстовый сценарий
        scenario = await screenwriter_run(brief)
        # Шаг 3: Режиссёр — сценарий → аудио + картинки + final.mp4
        await director_run(scenario, voice=voice)
        # После завершения director_run, файл final.mp4 должен находиться в корне проекта
        return {"filename": "final.mp4", "status": "done"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


if __name__ == "__main__":
    mcp.run()

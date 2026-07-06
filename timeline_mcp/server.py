import os
import sys
import logging

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from TTI import generate
from TTS import generate_text
from video.assembler import (
    assemble_video as _assemble_video,
    clear_manifest as _clear_manifest,
    preflight_assembly,
    save_scene as _save_scene,
)

logging.disable(logging.INFO)

mcp = FastMCP("timeline-tools")


@mcp.tool()
def preflight_video() -> dict:
    """Проверить, что локальная сборка видео готова до платных генераций."""
    return preflight_assembly()


@mcp.tool()
def clear_manifest() -> dict:
    """Очистить manifest перед новым роликом."""
    _clear_manifest()
    return {"status": "cleared"}


@mcp.tool()
async def generate_speech(text: str) -> dict:
    """Создать аудиофайл из текста озвучки."""
    filename, duration = await generate_text(text)
    return {"status": "ok", "filename": filename, "duration": duration}


@mcp.tool()
def generate_image(prompt: str) -> dict:
    """Создать вертикальное изображение 9:16 по промпту."""
    filename = generate(prompt)
    return {"status": "ok", "filename": filename}


@mcp.tool()
def add_scene(
    scene_number: int,
    image: str,
    audio: str,
    duration: float,
    text: str = "",
    motion: str = "zoom_in",
    zoom_start: float = 1.0,
    zoom_end: float = 1.12,
    pan_x: str = "center",
    pan_y: str = "center",
) -> dict:
    """Добавить одну сцену в manifest. JSON пишет код, не ИИ."""
    return _save_scene(
        scene_number=scene_number,
        image=image,
        audio=audio,
        duration=duration,
        text=text,
        motion=motion,
        zoom_start=zoom_start,
        zoom_end=zoom_end,
        pan_x=pan_x,
        pan_y=pan_y,
    )


@mcp.tool()
def assemble_video() -> dict:
    """Собрать final.mp4 из сцен manifest."""
    return _assemble_video()


if __name__ == "__main__":
    mcp.run()

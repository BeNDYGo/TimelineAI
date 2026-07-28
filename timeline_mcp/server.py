import os
import sys
import logging

from mcp.server.fastmcp import FastMCP
import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from TTI import generate
from TTS import generate_text
from config import ROOT, UPLOAD_POST_API_KEY, UPLOAD_POST_USER
from video.assembler import (
    assemble_video as _assemble_video,
    clear_manifest as _clear_manifest,
    save_scene as _save_scene,
)

logging.disable(logging.INFO)

mcp = FastMCP("timeline-tools")


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
    """Собрать итоговое видео из сцен manifest."""
    return _assemble_video()


@mcp.tool()
def publish_video(filename: str) -> dict:
    """Опубликовать итоговый видеофайл как Instagram Reel через Upload-Post."""
    if filename != os.path.basename(filename) or not filename.lower().endswith(".mp4"):
        raise ValueError("filename must be a bare .mp4 filename")
    if not UPLOAD_POST_API_KEY or not UPLOAD_POST_USER:
        raise RuntimeError("UPLOAD_POST_API_KEY and UPLOAD_POST_USER are missing in .env")

    video_path = ROOT / filename
    if not video_path.is_file():
        raise FileNotFoundError(f"Video not found: {filename}")

    with video_path.open("rb") as video:
        response = requests.post(
            "https://api.upload-post.com/api/upload",
            headers={"Authorization": f"Apikey {UPLOAD_POST_API_KEY}"},
            data={
                "user": UPLOAD_POST_USER,
                "platform[]": "instagram",
                "media_type": "REELS",
                "share_to_feed": "true",
            },
            files={"video": (filename, video, "video/mp4")},
            timeout=600,
        )

    try:
        result = response.json()
    except ValueError:
        raise RuntimeError(
            f"Upload-Post failed ({response.status_code}): {response.text[:500]}"
        ) from None
    if not response.ok or not result.get("success"):
        raise RuntimeError(f"Upload-Post failed ({response.status_code}): {result}")

    return {"status": "ok", "filename": filename, "result": result}


if __name__ == "__main__":
    mcp.run()

import subprocess
import uuid
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_block(audio: str, photo: str = None, video: str = None) -> str:
    """
    Склеивает визуал + аудио в mp4.

    Args:
        photo: Путь к изображению (jpg/png). Используется если не передан video.
        video: Путь к видео (mp4). Если передан — игнорирует photo.
        audio: Путь к аудиофайлу (wav/mp3).

    Returns:
        Имя выходного mp4 файла в корне проекта.
    """
    if not photo and not video:
        raise ValueError("Нужно передать photo или video")
    if not audio:
        raise ValueError("Нужно передать audio")

    input_visual = video if video else photo
    if not os.path.exists(input_visual):
        raise FileNotFoundError(f"Файл не найден: {input_visual}")
    if not os.path.exists(audio):
        raise FileNotFoundError(f"Файл не найден: {audio}")

    filename = f"video_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(ROOT, filename)

    is_photo = not video

    if is_photo:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", input_visual,
            "-i", audio,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-movflags", "+faststart",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", input_visual,
            "-i", audio,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            "-movflags", "+faststart",
            output_path,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr}")

    return filename

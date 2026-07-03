import json
import os
import subprocess
import tempfile
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(ROOT, "video", "manifest.json")

# Разрешение вертикального видео (9:16)
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FPS = 24


def _read_manifest() -> dict:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scenes": []}


def _write_manifest(data: dict):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clear_manifest():
    _write_manifest({"scenes": []})


def save_scene(scene_number: int, image: str, audio: str, duration: float) -> dict:
    manifest = _read_manifest()
    scene_data = {
        "scene": scene_number,
        "image": image,
        "audio": audio,
        "duration": duration,
    }
    manifest["scenes"].append(scene_data)
    manifest["scenes"].sort(key=lambda s: s["scene"])
    _write_manifest(manifest)
    return {"status": "saved", "scene": scene_number, "total": len(manifest["scenes"])}


def _get_duration(audio_path: str) -> float:
    """Получить длительность аудио через ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def _ken_burns_filter(duration: float, zoom_start: float = 1.0, zoom_end: float = 1.3) -> str:
    """
    Генерирует zoompan-фильтр ffmpeg для эффекта Ken Burns.
    Плавно зумит от zoom_start до zoom_end за время duration.
    """
    num_frames = int(duration * FPS)
    z_expr = f"{zoom_start}+({zoom_end}-{zoom_start})*on/{num_frames}"
    return (
        f"zoompan=z='{z_expr}':"
        f"d={num_frames}:"
        f"s={OUTPUT_WIDTH}x{OUTPUT_HEIGHT}:"
        f"fps={FPS}"
    )


def assemble_video(output_name: str = "final.mp4") -> dict:
    manifest = _read_manifest()
    scenes = sorted(manifest["scenes"], key=lambda s: s["scene"])

    if not scenes:
        return {"error": "No scenes in manifest"}

    temp_dir = tempfile.mkdtemp(prefix="timeline_")
    temp_clips = []

    try:
        for i, s in enumerate(scenes):
            img_path = os.path.join(ROOT, s["image"])
            aud_path = os.path.join(ROOT, s["audio"])

            if not os.path.exists(img_path):
                return {"error": f"Image not found: {s['image']}"}
            if not os.path.exists(aud_path):
                return {"error": f"Audio not found: {s['audio']}"}

            # Длительность из манифеста или ffprobe
            duration = s.get("duration", 0)
            if duration <= 0:
                duration = _get_duration(aud_path)

            clip_path = os.path.join(temp_dir, f"scene_{i:04d}.mp4")
            kb_filter = _ken_burns_filter(duration)

            # --- Шаг 1: изображение с zoompan → видео без звука ---
            # --- Шаг 2: добавить аудиодорожку ---
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", img_path,
                "-i", aud_path,
                "-filter_complex",
                f"[0:v]{kb_filter}[v]",
                "-map", "[v]",
                "-map", "1:a",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                clip_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    "error": f"FFmpeg failed on scene {i}: {result.stderr[:500]}",
                    "scene": s["scene"]
                }

            temp_clips.append(clip_path)

        if not temp_clips:
            return {"error": "No clips generated"}

        # Список клипов для конкатенации
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for clip_path in temp_clips:
                f.write(f"file '{clip_path}'\n")

        # Склейка всех сцен
        output_path = os.path.join(ROOT, output_name)
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            "-movflags", "+faststart",
            output_path
        ]

        result = subprocess.run(concat_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {
                "error": f"FFmpeg concat failed: {result.stderr[:500]}"
            }

        return {
            "status": "done",
            "filename": output_name,
            "scenes": len(scenes),
            "resolution": f"{OUTPUT_WIDTH}x{OUTPUT_HEIGHT}",
            "fps": FPS
        }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

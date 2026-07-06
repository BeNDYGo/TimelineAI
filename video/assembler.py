import json
import os
import subprocess
import tempfile
import shutil
from shutil import which

from video.subtitles import check_subtitle_dependencies, create_subtitle_overlays

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(ROOT, "video", "manifest.json")

# Разрешение вертикального видео (9:16)
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FPS = 24
MOTIONS = {"zoom_in", "zoom_out", "slow_zoom_in", "slow_zoom_out", "static"}
PAN_X = {"left", "center", "right"}
PAN_Y = {"top", "center", "bottom"}


def _ffmpeg_exe() -> str:
    ffmpeg = which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    if imageio_ffmpeg:
        return imageio_ffmpeg.get_ffmpeg_exe()
    raise RuntimeError("FFmpeg not found. Install ffmpeg or imageio-ffmpeg.")


FFMPEG = _ffmpeg_exe()


def preflight_assembly() -> dict:
    subtitle_status = check_subtitle_dependencies()
    if subtitle_status["status"] != "ok":
        return subtitle_status
    return {"status": "ok", "ffmpeg": FFMPEG}


def _read_manifest() -> dict:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scenes": []}


def _write_manifest(data: dict):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _asset_filename(asset: str) -> str:
    filename = str(asset).replace("\\", "/").split("/")[-1]
    if not filename:
        raise ValueError("asset filename is required")
    return filename


def _manifest_asset_path(asset: str) -> str:
    return f"VODS/{_asset_filename(asset)}"


def _resolve_asset_path(asset: str) -> str:
    return os.path.join(ROOT, "VODS", _asset_filename(asset))


def clear_manifest():
    _write_manifest({"scenes": []})


def _validate_scene_params(
    scene_number: int,
    image: str,
    audio: str,
    duration: float,
    motion: str,
    zoom_start: float,
    zoom_end: float,
    pan_x: str,
    pan_y: str,
) -> tuple[float, float, float]:
    if scene_number < 1:
        raise ValueError("scene_number must be >= 1")
    if not image:
        raise ValueError("image is required")
    if not audio:
        raise ValueError("audio is required")
    duration = float(duration)
    if duration <= 0:
        raise ValueError("duration must be > 0")
    if motion not in MOTIONS:
        raise ValueError(f"motion must be one of: {', '.join(sorted(MOTIONS))}")
    zoom_start = float(zoom_start)
    zoom_end = float(zoom_end)
    if zoom_start <= 0 or zoom_end <= 0:
        raise ValueError("zoom_start and zoom_end must be > 0")
    if pan_x not in PAN_X:
        raise ValueError(f"pan_x must be one of: {', '.join(sorted(PAN_X))}")
    if pan_y not in PAN_Y:
        raise ValueError(f"pan_y must be one of: {', '.join(sorted(PAN_Y))}")
    return duration, zoom_start, zoom_end


def save_scene(
    scene_number: int,
    image: str,
    audio: str,
    duration: float,
    text: str = "",
    motion: str = "zoom_in",
    zoom_start: float = 1.0,
    zoom_end: float = 1.3,
    pan_x: str = "center",
    pan_y: str = "center",
) -> dict:
    duration, zoom_start, zoom_end = _validate_scene_params(
        scene_number,
        image,
        audio,
        duration,
        motion,
        zoom_start,
        zoom_end,
        pan_x,
        pan_y,
    )
    manifest = _read_manifest()
    scene_data = {
        "scene": scene_number,
        "image": _manifest_asset_path(image),
        "audio": _manifest_asset_path(audio),
        "duration": duration,
        "text": text,
        "motion": motion,
        "zoom_start": zoom_start,
        "zoom_end": zoom_end,
        "pan_x": pan_x,
        "pan_y": pan_y,
    }
    manifest["scenes"].append(scene_data)
    manifest["scenes"].sort(key=lambda s: s["scene"])
    _write_manifest(manifest)
    return {"status": "saved", "scene": scene_number, "total": len(manifest["scenes"])}


def _get_duration(audio_path: str) -> float:
    """Получить длительность аудио через ffprobe."""
    result = subprocess.run(
        [
            which("ffprobe") or "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def _pan_expr(axis: str, value: str) -> str:
    positions = {
        "x": {
            "left": "0",
            "center": "iw/2-(iw/zoom/2)",
            "right": "iw-iw/zoom",
        },
        "y": {
            "top": "0",
            "center": "ih/2-(ih/zoom/2)",
            "bottom": "ih-ih/zoom",
        },
    }
    return positions[axis].get(value, positions[axis]["center"])


def _motion_defaults(motion: str, zoom_start: float, zoom_end: float) -> tuple[float, float]:
    if motion == "static":
        return 1.0, 1.0
    if motion == "zoom_out" and zoom_start == 1.0 and zoom_end == 1.3:
        return 1.3, 1.0
    if motion == "slow_zoom_in" and zoom_start == 1.0 and zoom_end == 1.3:
        return 1.0, 1.12
    if motion == "slow_zoom_out" and zoom_start == 1.0 and zoom_end == 1.3:
        return 1.12, 1.0
    return zoom_start, zoom_end


def _ken_burns_filter(
    duration: float,
    zoom_start: float = 1.0,
    zoom_end: float = 1.3,
    pan_x: str = "center",
    pan_y: str = "center",
) -> str:
    """
    Генерирует zoompan-фильтр ffmpeg для эффекта Ken Burns.
    Плавно зумит от zoom_start до zoom_end за время duration.
    """
    num_frames = max(1, int(duration * FPS))
    z_expr = f"{zoom_start}+({zoom_end}-{zoom_start})*on/{num_frames}"
    x_expr = _pan_expr("x", pan_x)
    y_expr = _pan_expr("y", pan_y)
    return (
        f"zoompan=z='{z_expr}':"
        f"x='{x_expr}':"
        f"y='{y_expr}':"
        f"d={num_frames}:"
        f"s={OUTPUT_WIDTH}x{OUTPUT_HEIGHT}:"
        f"fps={FPS}"
    )


def _burn_subtitle_overlays(input_path: str, output_path: str, overlays: list[dict]) -> dict | None:
    if not overlays:
        shutil.copyfile(input_path, output_path)
        return None

    subtitle_video = os.path.join(os.path.dirname(output_path), f"{os.path.basename(output_path)}.subtitles.mov")
    subtitle_error = _build_subtitle_video(overlays, subtitle_video)
    if subtitle_error:
        return subtitle_error

    cmd = [
        FFMPEG, "-y",
        "-i", input_path,
        "-i", subtitle_video,
        "-filter_complex", "[0:v][1:v]overlay=0:0:eof_action=pass:format=auto[v]",
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        "-movflags", "+faststart",
        "-shortest",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"error": f"FFmpeg subtitle overlays failed: {result.stderr[:500]}"}
    return None


def _build_subtitle_video(overlays: list[dict], output_path: str) -> dict | None:
    from PIL import Image

    temp_dir = os.path.dirname(output_path)
    blank_path = os.path.join(temp_dir, "subtitle_blank.png")
    Image.new("RGBA", (OUTPUT_WIDTH, OUTPUT_HEIGHT), (0, 0, 0, 0)).save(blank_path)

    concat_path = os.path.join(temp_dir, f"{os.path.basename(output_path)}.txt")
    entries = []
    cursor = 0.0

    for overlay in sorted(overlays, key=lambda item: item["start"]):
        start = float(overlay["start"])
        end = float(overlay["end"])
        if start > cursor:
            entries.append((blank_path, start - cursor))
        if end > start:
            entries.append((overlay["path"], end - start))
            cursor = end

    if not entries:
        return None

    with open(concat_path, "w", encoding="utf-8") as f:
        for path, duration in entries:
            f.write(f"file '{path}'\n")
            f.write(f"duration {duration:.3f}\n")
        f.write(f"file '{entries[-1][0]}'\n")

    cmd = [
        FFMPEG, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_path,
        "-vf", f"fps={FPS},format=rgba",
        "-c:v", "qtrle",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"error": f"FFmpeg subtitle video failed: {result.stderr[:500]}"}
    return None


def assemble_video(output_name: str = "final.mp4") -> dict:
    subtitle_status = check_subtitle_dependencies()
    if subtitle_status["status"] != "ok":
        return subtitle_status

    manifest = _read_manifest()
    scenes = sorted(manifest["scenes"], key=lambda s: s["scene"])

    if not scenes:
        return {"error": "No scenes in manifest"}

    temp_dir = tempfile.mkdtemp(prefix="timeline_")
    temp_clips = []

    try:
        for i, s in enumerate(scenes):
            img_path = _resolve_asset_path(s["image"])
            aud_path = _resolve_asset_path(s["audio"])

            if not os.path.exists(img_path):
                return {"error": f"Image not found: {s['image']}"}
            if not os.path.exists(aud_path):
                return {"error": f"Audio not found: {s['audio']}"}

            # Длительность из манифеста или ffprobe
            duration = s.get("duration", 0)
            if duration <= 0:
                duration = _get_duration(aud_path)

            raw_clip_path = os.path.join(temp_dir, f"scene_{i:04d}_raw.mp4")
            clip_path = os.path.join(temp_dir, f"scene_{i:04d}.mp4")
            motion = s.get("motion", "zoom_in")
            zoom_start, zoom_end = _motion_defaults(
                motion,
                float(s.get("zoom_start", 1.0)),
                float(s.get("zoom_end", 1.3)),
            )
            kb_filter = _ken_burns_filter(
                duration,
                zoom_start=zoom_start,
                zoom_end=zoom_end,
                pan_x=s.get("pan_x", "center"),
                pan_y=s.get("pan_y", "center"),
            )

            # --- Шаг 1: изображение с zoompan → видео без звука ---
            # --- Шаг 2: добавить аудиодорожку ---
            cmd = [
                FFMPEG, "-y",
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
                raw_clip_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    "error": f"FFmpeg failed on scene {i}: {result.stderr[:500]}",
                    "scene": s["scene"]
                }

            overlays = create_subtitle_overlays([s], os.path.join(temp_dir, f"subtitles_{i:04d}"))
            subtitle_error = _burn_subtitle_overlays(raw_clip_path, clip_path, overlays)
            if subtitle_error:
                subtitle_error["scene"] = s["scene"]
                return subtitle_error

            temp_clips.append(clip_path)

        if not temp_clips:
            return {"error": "No clips generated"}

        # Список клипов для конкатенации
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for clip_path in temp_clips:
                f.write(f"file '{clip_path}'\n")

        output_path = os.path.join(ROOT, output_name)
        concat_cmd = [
            FFMPEG, "-y",
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
            "fps": FPS,
            "subtitles": "per_scene"
        }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

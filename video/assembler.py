import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(ROOT, "video", "manifest.json")


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


def assemble_video() -> dict:
    manifest = _read_manifest()
    scenes = sorted(manifest["scenes"], key=lambda s: s["scene"])

    if not scenes:
        return {"error": "No scenes in manifest"}

    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

    clips = []
    for s in scenes:
        img_path = os.path.join(ROOT, s["image"])
        aud_path = os.path.join(ROOT, s["audio"])

        if not os.path.exists(img_path):
            return {"error": f"Image not found: {s['image']}"}
        if not os.path.exists(aud_path):
            return {"error": f"Audio not found: {s['audio']}"}

        audio_clip = AudioFileClip(aud_path)
        video_clip = ImageClip(img_path).with_duration(audio_clip.duration)
        video_clip = video_clip.resized((1920, 1080))
        video_clip = video_clip.with_audio(audio_clip)
        clips.append(video_clip)

    final = concatenate_videoclips(clips, method="compose")
    output_path = os.path.join(ROOT, "final.mp4")
    final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    for clip in clips:
        clip.close()
    final.close()

    return {"status": "done", "filename": "final.mp4", "scenes": len(scenes)}

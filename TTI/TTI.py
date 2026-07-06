import base64
import sys
import uuid
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import ROUTERAI_API_KEY, ROUTERAI_BASE_URL, VODS

MODEL = "bytedance-seed/seedream-4.5"
IMAGES_URL = f"{ROUTERAI_BASE_URL}/images"


def _unique_filename(prefix: str, suffix: str) -> str:
    while True:
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}{suffix}"
        if not (VODS / filename).exists():
            return filename


def generate_image(prompt: str) -> str:
    """Генерирует изображение по промпту и возвращает имя файла."""
    payload = {
        "model": "bytedance-seed/seedream-4.5",
        "prompt": prompt,
        "n": 1,
        "aspect_ratio": "9:16",
        "resolution": "4K"
    }

    try:
        response = requests.post(
            IMAGES_URL,
            headers={
                "Authorization": f"Bearer {ROUTERAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
        if not response.ok:
            raise RuntimeError(
                f"RouterAI image error {response.status_code}: {response.text[:1000]}"
            )
        result = response.json()
    except Exception as e:
        print(f"[TTI ERROR] {e}")
        raise
    
    if not result.get("data"):
        raise RuntimeError("No image generated")
    
    b64_data = result["data"][0].get("b64_json")
    if not b64_data:
        raise RuntimeError("Image response has no b64_json")

    filename = _unique_filename("generated", ".png")
    VODS.mkdir(exist_ok=True)
    file_path = VODS / filename
    
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(b64_data))
    
    return filename


def generate(prompt: str) -> str:
    return generate_image(prompt)


if __name__ == "__main__":
    prompt = input("Введите prompt: ").strip()

    filename = generate_image(prompt)
    print(filename)

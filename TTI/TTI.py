import requests
import base64
import uuid
import os

from config import ROUTERAI_API_KEY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = "bytedance-seed/seedream-4.5"
ASPECT_RATIO = "9:16"


def _unique_filename(prefix: str, suffix: str) -> str:
    while True:
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}{suffix}"
        if not os.path.exists(os.path.join(ROOT, filename)):
            return filename


def generate(prompt: str, image: str = None) -> str:
    """Генерирует изображение по промпту, опционально используя референс-изображение
    
    Args:
        prompt: Текстовое описание изображения
        image: Имя файла референс-изображения в корне проекта (опционально)
    
    Returns:
        Имя сгенерированного файла в корне проекта
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": 1,
        "aspect_ratio": ASPECT_RATIO,
    }
    
    if image:
        image_path = os.path.join(ROOT, image)
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
                payload["input_references"] = [{
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                }]
    
    try:
        response = requests.post(
            "https://routerai.ru/api/v1/images",
            headers={
                "Authorization": f"Bearer {ROUTERAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
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
    
    b64_data = result["data"][0]["b64_json"]
    filename = _unique_filename("generated", ".png")
    file_path = os.path.join(ROOT, filename)
    
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(b64_data))
    
    return filename

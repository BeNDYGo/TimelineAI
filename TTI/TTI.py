import requests
import base64
import uuid
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = "sk-OzdSe28mYq9sODbaCjeD8kJ5ASdz7-PE"
MODEL = "bytedance-seed/seedream-4.5"

def generate(prompt: str, image: str = None, aspect_ratio: str = "auto") -> str:
    """Генерирует изображение по промпту, опционально используя референс-изображение
    
    Args:
        prompt: Текстовое описание изображения
        image: Имя файла референс-изображения в корне проекта (опционально)
        aspect_ratio: Соотношение сторон (16:9, 9:16, 1:1, auto)
    
    Returns:
        Имя сгенерированного файла в корне проекта
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": 1,
        "resolution": "1K",
        "aspect_ratio": aspect_ratio,
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
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        print(f"[TTI ERROR] {e}")
        raise
    
    if not result.get("data"):
        raise RuntimeError("No image generated")
    
    b64_data = result["data"][0]["b64_json"]
    filename = f"generated_{uuid.uuid4().hex}.png"
    file_path = os.path.join(ROOT, filename)
    
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(b64_data))
    
    return filename

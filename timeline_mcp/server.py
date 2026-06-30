import sys
import os
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from TTS import generateText
from TTI import generate


mcp = FastMCP("timeline-tools")


@mcp.tool()
def generate_speech(voice_style: str, lang: str, text: str) -> dict:
    """
    Превращает текст в аудиофайл
    
    Args:
        voice_style: Стиль голоса. Доступны женские (F1, F2, F3, F4, F5) и мужские (M1, M2, M3, M4, M5).
        lang: Код языка в формате ISO (например, 'ru', 'en').
        text: Текст который будет озвучен
    Returns:
        путь к файлу и длительность в json формате
    """
    filename, duration = generateText(voice_style, lang, text)
    return {"filename": filename, "duration": duration}


@mcp.tool()
def generate_image(prompt: str, image: str = None, aspect_ratio: str = "auto") -> dict:
    """Сгенерировать кадр по текстовому описанию
    
    Args:
        prompt: Текстовое описание изображения
        image: Имя файла референс-изображения в корне проекта (опционально)
        aspect_ratio: Соотношение сторон изображения. Доступные значения: 16:9, 9:16, 1:1, auto.
                   Если по контексту не понятно - укажите auto.
    
    Returns:
        Имя сгенерированного файла
    """
    return {"filename": generate(prompt, image=image, aspect_ratio=aspect_ratio)}


if __name__ == "__main__":
    mcp.run()

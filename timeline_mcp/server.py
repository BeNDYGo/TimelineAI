import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from TTS import generateText
from TTI import generate
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("timeline-tools")


@mcp.tool()
def generate_speech(voice_style: str, lang: str, text: str) -> dict:
    """Озвучить текст голосом"""
    filename, duration = generateText(voice_style, lang, text)
    return {"filename": filename, "duration": duration}


@mcp.tool()
def generate_image(prompt: str) -> dict:
    """Сгенерировать кадр по текстовому описанию"""
    return {"filename": generate(prompt)}


if __name__ == "__main__":
    mcp.run()

from openai import AsyncOpenAI
import json
from prompts import SCREENWRITER_PROMPT
from log import banner, thinking, result, SCREENWRITER_COLOR

client = AsyncOpenAI(base_url="https://routerai.ru/api/v1", api_key="sk-OzdSe28mYq9sODbaCjeD8kJ5ASdz7-PE")
model = "deepseek/deepseek-v4-flash"


def _parse_scenes(text: str) -> dict:
    """Извлекает JSON-сценарий (character_description + scenes) из ответа LLM."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    data = json.loads(text)
    if isinstance(data, list):
        return {"character_description": "", "scenes": data}
    return data


async def run(brief: str) -> dict:
    banner("СЦЕНАРИСТ", SCREENWRITER_COLOR)
    thinking("Сценарист", SCREENWRITER_COLOR, "Пишу сценарий по брифу...")

    messages = [
        {"role": "system", "content": SCREENWRITER_PROMPT},
        {"role": "user", "content": brief},
    ]

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
    )

    raw = response.choices[0].message.content
    scenario = _parse_scenes(raw)
    scenes = scenario.get("scenes", [])

    result("Сценарист", SCREENWRITER_COLOR, f"Сценарий готов: {len(scenes)} сцен")
    if scenario.get("character_description"):
        print(f"  Персонаж: {scenario['character_description'][:80]}...")
    for s in scenes:
        print(f"  Сцена {s['scene_number']}: {s['narration'][:60]}...")
    print()
    return scenario

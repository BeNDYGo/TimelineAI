from openai import AsyncOpenAI
from prompts import SCREENWRITER_PROMPT
from log import banner, thinking, result, SCREENWRITER_COLOR

client = AsyncOpenAI(base_url="https://routerai.ru/api/v1", api_key="sk-OzdSe28mYq9sODbaCjeD8kJ5ASdz7-PE")
model = "deepseek/deepseek-v4-flash"


async def run(brief: str) -> str:
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

    scenario_text = response.choices[0].message.content
    result("Сценарист", SCREENWRITER_COLOR, "Сценарий готов:")
    print(f"\n{scenario_text}\n")
    return scenario_text

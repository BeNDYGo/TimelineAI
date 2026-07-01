from openai import AsyncOpenAI
from prompts import PRODUCER_PROMPT
from log import banner, thinking, result, PRODUCER_COLOR

client = AsyncOpenAI(base_url="https://routerai.ru/api/v1", api_key="sk-OzdSe28mYq9sODbaCjeD8kJ5ASdz7-PE")
model = "deepseek/deepseek-v4-flash"


async def run(topic: str) -> str:
    banner("ПРОДЮССЕР", PRODUCER_COLOR)
    thinking("Продюссер", PRODUCER_COLOR, f"Анализирую тему: {topic}")

    messages = [
        {"role": "system", "content": PRODUCER_PROMPT},
        {"role": "user", "content": topic},
    ]

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
    )

    brief = response.choices[0].message.content
    result("Продюссер", PRODUCER_COLOR, "Бриф готов:")
    print(f"\n{brief}\n")
    return brief

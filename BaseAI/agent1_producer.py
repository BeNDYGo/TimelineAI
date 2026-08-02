from openai import AsyncOpenAI

from config import ROUTERAI_API_KEY, ROUTERAI_BASE_URL
from log import PRODUCER_COLOR, banner, result, thinking
from prompts import STORY_AUTHOR_PROMPT


client = AsyncOpenAI(base_url=ROUTERAI_BASE_URL, api_key=ROUTERAI_API_KEY)
model = "deepseek/deepseek-v4-flash"


async def run(topic: str, project_context: str) -> str:
    banner("АВТОР ИСТОРИИ", PRODUCER_COLOR)
    thinking("Автор", PRODUCER_COLOR, f"Пишу готовую байку по идее: {topic}")

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"{STORY_AUTHOR_PROMPT}\n\nКОНТЕКСТ ПРОЕКТА:\n{project_context}",
            },
            {"role": "user", "content": topic},
        ],
    )

    story = response.choices[0].message.content or ""
    result("Автор", PRODUCER_COLOR, "История готова:")
    print(f"\n{story}\n")
    return story

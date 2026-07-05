from openai import AsyncOpenAI

from config import ROUTERAI_API_KEY, ROUTERAI_BASE_URL
from log import SCREENWRITER_COLOR, banner, result, thinking
from prompts import STORYBOARD_PROMPT


client = AsyncOpenAI(base_url=ROUTERAI_BASE_URL, api_key=ROUTERAI_API_KEY)
model = "deepseek/deepseek-v4-flash"


async def run(story: str) -> str:
    banner("РАСКАДРОВЩИК", SCREENWRITER_COLOR)
    thinking("Раскадровщик", SCREENWRITER_COLOR, "Пишу текстовую раскадровку по шаблону...")

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": STORYBOARD_PROMPT},
            {"role": "user", "content": story},
        ],
    )

    storyboard = response.choices[0].message.content or ""
    result("Раскадровщик", SCREENWRITER_COLOR, "Раскадровка готова:")
    print(f"\n{storyboard}\n")
    return storyboard

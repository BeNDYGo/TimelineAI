import asyncio
import os
import sys
from pathlib import Path


sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "BaseAI"))

from agent1_producer import run as story_run
from agent2_screenwriter import run as storyboard_run
from agent3_director import run as production_run


PROJECT_FILE = Path(__file__).with_name("core.md")


async def main():
    print("\n" + "=" * 55)
    print("  TimelineAI - генератор коротких баек")
    print("=" * 55 + "\n")

    project_context = PROJECT_FILE.read_text(encoding="utf-8").strip()
    if not project_context:
        raise ValueError(f"Файл проекта пуст: {PROJECT_FILE}")

    idea = input("Введите идею ролика: ").strip()
    if not idea:
        print("Идея не может быть пустой.")
        return

    story = await story_run(idea, project_context)
    storyboard = await storyboard_run(story, project_context)
    await production_run(storyboard)

    print("\n" + "=" * 55)
    print("  ГОТОВО")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

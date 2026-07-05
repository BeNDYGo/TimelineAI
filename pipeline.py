import asyncio
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "BaseAI"))

from agent1_producer import run as story_run
from agent2_screenwriter import run as storyboard_run
from agent3_director import run as production_run


async def main():
    print("\n" + "=" * 55)
    print("  TimelineAI - генератор коротких баек")
    print("=" * 55 + "\n")

    idea = input("Введите идею ролика: ").strip()
    if not idea:
        print("Идея не может быть пустой.")
        return

    story = await story_run(idea)
    storyboard = await storyboard_run(story)
    await production_run(storyboard)

    print("\n" + "=" * 55)
    print("  ГОТОВО: final.mp4")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

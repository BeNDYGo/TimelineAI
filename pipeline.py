import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "BaseAI"))

from agent1_producer import run as producer_run
from agent2_screenwriter import run as screenwriter_run
from agent3_director import run as director_run
from log import banner


async def main():
    print("\n" + "=" * 55)
    print("  TimelineAI — Создание видео-ролика")
    print("=" * 55 + "\n")

    topic = input("Введите тему ролика: ").strip()
    if not topic:
        print("Тема не может быть пустой.")
        return

    voice = input("Голос (m — мужской, w — женский) [m]: ").strip() or "m"

    # Шаг 1: Продюссер — тема → бриф
    brief = await producer_run(topic)
    #input("\n--- Нажмите Enter чтобы передать бриф сценаристу ---")

    # Шаг 2: Сценарист — бриф → текстовый сценарий
    scenario_text = await screenwriter_run(brief)
    #input("\n--- Нажмите Enter чтобы начать генерацию файлов ---")

    # Шаг 3: Режиссёр — сценарий → аудио + картинки + final.mp4
    await director_run(scenario_text, voice=voice)

    print("\n" + "=" * 55)
    print("  ГОТОВО! Все файлы созданы.")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

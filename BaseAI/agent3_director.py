from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import sys
import os
from prompts import DIRECTOR_PROMPT
from log import banner, thinking, result, DIRECTOR_COLOR
from video.assembler import clear_manifest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

client = AsyncOpenAI(base_url="https://routerai.ru/api/v1", api_key="sk-OzdSe28mYq9sODbaCjeD8kJ5ASdz7-PE")
model = "deepseek/deepseek-v4-flash"

_mcp_session = None
_mcp_cm = None


async def init_mcp():
    global _mcp_cm, _mcp_session
    _mcp_cm = stdio_client(
        StdioServerParameters(
            command=sys.executable,
            args=["timeline_mcp/server.py"],
            cwd=ROOT,
        )
    )
    read, write = await _mcp_cm.__aenter__()
    _mcp_session = ClientSession(read, write)
    await _mcp_session.__aenter__()
    await _mcp_session.initialize()


async def close_mcp():
    global _mcp_cm, _mcp_session
    if _mcp_session:
        await _mcp_session.__aexit__(None, None, None)
        _mcp_session = None
    if _mcp_cm:
        await _mcp_cm.__aexit__(None, None, None)
        _mcp_cm = None


async def _tools():
    result = await _mcp_session.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.inputSchema,
            },
        }
        for t in result.tools
    ]


async def run(scenario: dict, voice: str = "M1", lang: str = "ru") -> list:
    banner("РЕЖИССЁР", DIRECTOR_COLOR)

    scenes = scenario.get("scenes", [])
    if not scenes:
        thinking("Режиссёр", DIRECTOR_COLOR, "Нет сцен для обработки!")
        return []

    thinking("Режиссёр", DIRECTOR_COLOR, "Очищаю манифест...")
    clear_manifest()

    thinking("Режиссёр", DIRECTOR_COLOR, "Инициализирую MCP...")
    await init_mcp()

    scenario_text = json.dumps(scenario, ensure_ascii=False, indent=2)
    user_msg = (
        f"Сценарий:\n{scenario_text}\n\n"
        f"Голос: {voice}\n"
        f"Язык: {lang}\n\n"
        f"Сгенерируй аудио и изображения для КАЖДОЙ сцены, сохрани через save_scene, затем собери видео через assemble_video."
    )

    messages = [
        {"role": "system", "content": DIRECTOR_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    thinking("Режиссёр", DIRECTOR_COLOR, f"Начинаю продакшен {len(scenes)} сцен...")

    # 3 tools per scene (speech + image + save) + assemble_video + запас
    max_steps = len(scenes) * 3 + 2
    for step in range(max_steps):
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=await _tools(),
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if msg.content:
            result("Режиссёр", DIRECTOR_COLOR, msg.content)

        if not msg.tool_calls:
            break

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            thinking("Режиссёр", DIRECTOR_COLOR, f"Вызов: {tc.function.name}({args})")
            mcp_result = await _mcp_session.call_tool(tc.function.name, args)
            content = mcp_result.content[0].text
            result("Режиссёр", DIRECTOR_COLOR, f"Результат: {content}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": content,
                }
            )

    await close_mcp()
    return messages

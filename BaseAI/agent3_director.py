import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

from config import ROUTERAI_API_KEY, ROUTERAI_BASE_URL
from log import DIRECTOR_COLOR, RESET
from prompts import PRODUCTION_PROMPT


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

client = AsyncOpenAI(base_url=ROUTERAI_BASE_URL, api_key=ROUTERAI_API_KEY)
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
    tool_result = await _mcp_session.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in tool_result.tools
    ]


def _tool_content(mcp_result) -> str:
    if not mcp_result.content:
        return ""
    return mcp_result.content[0].text


def _raise_on_tool_error(tool_name: str, mcp_result, content: str) -> None:
    if getattr(mcp_result, "isError", False):
        raise RuntimeError(f"{tool_name} failed: {content}")

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return

    status = data.get("status")
    if status and status != "ok" and status not in {"cleared", "saved", "done"}:
        raise RuntimeError(f"{tool_name} failed: {content}")
    if "error" in data:
        raise RuntimeError(f"{tool_name} failed: {content}")


async def run(storyboard: str) -> list:
    await init_mcp()

    messages = [
        {"role": "system", "content": PRODUCTION_PROMPT},
        {"role": "user", "content": f"Раскадровка:\n\n{storyboard}"},
    ]

    try:
        for _ in range(60):
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=await _tools(),
            )
            msg = response.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))

            if msg.content:
                print(f"{DIRECTOR_COLOR}{msg.content}{RESET}")

            if not msg.tool_calls:
                return messages

            for tool_call in msg.tool_calls:
                args = json.loads(tool_call.function.arguments or "{}")
                mcp_result = await _mcp_session.call_tool(tool_call.function.name, args)
                content = _tool_content(mcp_result)
                _raise_on_tool_error(tool_call.function.name, mcp_result, content)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": content,
                    }
                )

        raise RuntimeError("Производственный агент превысил лимит шагов")
    finally:
        await close_mcp()

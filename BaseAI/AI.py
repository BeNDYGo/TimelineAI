from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import json
import os
import sys
from system_prompt import SYSTEM_PROMPT
from config import ROUTERAI_API_KEY, ROUTERAI_BASE_URL


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key="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")
#model = "meta-llama/llama-3.3-70b-instruct:free" #meta-llama/llama-3.3-70b-instruct:free   # openai/gpt-oss-20b:free

client = AsyncOpenAI(base_url=ROUTERAI_BASE_URL, api_key=ROUTERAI_API_KEY)
model = "deepseek/deepseek-v4-flash"

_stdio_cm = None
_session = None


async def init_mcp():
    global _stdio_cm, _session
    _stdio_cm = stdio_client(
        StdioServerParameters(
            command=sys.executable, args=["timeline_mcp/server.py"], cwd=ROOT
        )
    )
    read, write = await _stdio_cm.__aenter__()
    _session = ClientSession(read, write)
    await _session.__aenter__()
    await _session.initialize()


async def close_mcp():
    global _stdio_cm, _session
    if _session:
        await _session.__aexit__(None, None, None)
        _session = None
    if _stdio_cm:
        await _stdio_cm.__aexit__(None, None, None)
        _stdio_cm = None


async def _tools():
    result = await _session.list_tools()
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


async def chat(message: str, history: list) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [
        {"role": "user", "content": m["user"]}
        if "user" in m
        else {"role": "assistant", "content": m["assistant"]}
        for m in history
    ]
    messages.append({"role": "user", "content": message})

    for _ in range(4):
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=await _tools(),
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return msg.content or ""

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = await _session.call_tool(tc.function.name, args)
            content = result.content[0].text
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": content,
                }
            )

    return "Превышен лимит шагов."


async def _main():
    await init_mcp()
    try:
        history = []
        while True:
            user_message = input("\nВы: ")
            response = await chat(user_message, history)
            history.append({"user": user_message, "assistant": response})
            print(f"\nAI: {response}")
    finally:
        await close_mcp()


if __name__ == "__main__":
    asyncio.run(_main())

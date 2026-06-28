import asyncio
import json
import os
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


class MCPManager:
    def __init__(self, servers: dict[str, str]):
        self.servers = servers
        self.clients = {}
        self.tools = []  # in OpenAI format
        self._stack = AsyncExitStack()

    async def __aenter__(self):
        for url in self.servers.values():
            # initialize MCP session with Streamable HTTP client
            read, write, session_id = await self._stack.enter_async_context(
                streamable_http_client(url)
            )
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            # use /list_tools MCP endpoint to get tools
            # parse each one to get OpenAI-compatible schema
            tools_resp = await session.list_tools()
            for t in tools_resp.tools:
                self.clients[t.name] = session
                self.tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema,
                        },
                    }
                )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._stack.aclose()

    async def call_tool(self, name: str, args: dict) -> dict | str:
        # call the MCP tool with given arguments
        result = await self.clients[name].call_tool(name, arguments=args)
        return result.content[0].text


async def make_llm_request(prompt: str) -> str:
    mcp_servers = {
        "weather_forecast": "http://localhost:8001/mcp",
        "date_time_server": "http://localhost:8002/mcp",
    }

    load_dotenv()
    client = OpenAI(
        api_key=os.environ["GEMINI_API_KEY"],
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    async with MCPManager(mcp_servers) as mcp:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Use tools if you need to."
                    # "If the task is impossible based on your knowledge and tools, "
                    # "return that information."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        # guard: loop limit, we break as soon as we get an answer
        for _ in range(10):
            response = client.chat.completions.create(
                model="gemini-3.5-flash",
                messages=messages,
                tools=mcp.tools,
                tool_choice="auto",
                max_completion_tokens=1000,
                reasoning_effort="low",
            )

            response = response.choices[0].message
            if not response.tool_calls:
                return response.content

            messages.append(response.model_dump(exclude_none=True))
            for tool_call in response.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                print(f"Executing tool '{func_name}'")
                func_result = await mcp.call_tool(func_name, func_args)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": str(func_result),
                    }
                )


if __name__ == "__main__":
    prompt = "What will be weather in Birmingham, UK in two weeks?"
    response = asyncio.run(make_llm_request(prompt))
    print("Response:\n", response)

    print()

    prompt = "What will be weather in Warsaw the day after tomorrow?"
    response = asyncio.run(make_llm_request(prompt))
    print("Response:\n", response)

    print()

    prompt = "What will be weather in New York in two months?"
    response = asyncio.run(make_llm_request(prompt))
    print("Response:\n", response)

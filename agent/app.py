import asyncio
import json
import os
from typing import Optional, Any

from mcp import Resource, Tool
from mcp.types import Prompt

from agent.mcp_client import MCPClient
from agent.dial_client import DialClient
from agent.models.message import Message, Role
from agent.prompts import SYSTEM_PROMPT


# https://remote.mcpservers.org/fetch/mcp
# Pay attention that `fetch` doesn't have resources and prompts

API_KEY = os.getenv('API_KEY', '')
DIAL_URL = 'https://ai-proxy.lab.epam.com'

async def main():
    async with MCPClient(mcp_server_url='http://localhost:8005/mcp') as mcp_client:
        print('initializing resources...')
        await init_resources(mcp_client)

        print('initializing tools...')
        tools = await init_tools(mcp_client)
        dial_client = DialClient(endpoint=DIAL_URL, api_key=API_KEY, tools=tools, mcp_client=mcp_client)

        print('fetching prompts from mcp server...')
        messages = await init_messages(mcp_client)

        print('What can I assist you with today?')
        while True:
            user_input = input('> ')
            if user_input == 'exit':
                break
            messages.append(Message(role=Role.USER, content=user_input))
            reply = await dial_client.get_completion(messages=messages)
            messages.append(reply)


async def init_resources(mcp_client: MCPClient) -> list[Resource]:
    resources = await mcp_client.get_resources()
    for resource in resources:
        print(resource)
    return resources

async def init_tools(mcp_client: MCPClient) -> list[dict[str, Any]]:
    tools = await mcp_client.get_tools()
    for tool in tools:
        print(f"tool definition: {json.dumps(tool, indent=2)}")
    return tools

async def init_messages(mcp_client: MCPClient) -> list[Message]:
    prompts = await mcp_client.get_prompts()
    messages = [
        Message(role=Role.SYSTEM, content=SYSTEM_PROMPT),
    ]
    print("\n=== Available Prompts ===")
    prompts: list[Prompt] = await mcp_client.get_prompts()
    for prompt in prompts:
        print(prompt)
        content = await mcp_client.get_prompt(prompt.name)
        print(content)
        messages.append(
            Message(
                role=Role.USER,
                content=f"## Prompt provided by MCP server:\n{prompt.description}\n{content}"
            )
        )

    print("MCP-based Agent is ready! Type your query or 'exit' to exit.")
    return messages

if __name__ == "__main__":
    asyncio.run(main())

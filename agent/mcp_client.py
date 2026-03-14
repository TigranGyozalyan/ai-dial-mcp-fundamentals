from typing import Optional, Any

from mcp import ClientSession, ListToolsResult, ListResourcesResult, ListPromptsResult
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult, TextContent, GetPromptResult, ReadResourceResult, Resource, TextResourceContents, \
    BlobResourceContents, Prompt
from pydantic import AnyUrl


class MCPClient:
    """Handles MCP server connection and tool execution"""

    def __init__(self, mcp_server_url: str) -> None:
        self.mcp_server_url = mcp_server_url
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None

    async def __aenter__(self):
        self._streams_context = streamablehttp_client(self.mcp_server_url)
        read_stream, write_stream, _ = await self._streams_context.__aenter__()
        self._session_context = ClientSession(read_stream, write_stream)
        self.session = await self._session_context.__aenter__()
        # TODO:
        # 1. Call `streamablehttp_client` method with `mcp_server_url` and assign to `self._streams_context`
        # 2. Call `await self._streams_context.__aenter__()` and assign to `read_stream, write_stream, _`
        # 3. Create `ClientSession(read_stream, write_stream)` and assign to `self._session_context`
        # 4. Call `await self._session_context.__aenter__()` and assign it to `self.session`
        # 5. Call `self.session.initialize()`, and print its result (to check capabilities of MCP server later)
        # 6. return self

        await self.session.initialize()
        print('mcp client connected')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        await self._streams_context.__aexit__(exc_type, exc_val, exc_tb)
        # TODO:
        # This is shutdown method.
        # If session is present and session context is present as well then shutdown the session context (__aexit__ method with params)
        # If streams context is present then shutdown the streams context (__aexit__ method with params)

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        tool_res: ListToolsResult = await self.session.list_tools()
        tools = tool_res.tools
        return [
            {
                'type': 'function',
                'function': {
                    'description': tool.description,
                    'parameters': tool.inputSchema,
                    'name': tool.name
                }
            }
            for tool in tools]
        # TODO:
        # 1. Call `await self.session.list_tools()` and assign to `tools`
        # 2. Return list with dicts with tool schemas. It should be provided according to DIAL specification
        #    https://dialx.ai/dial_api#operation/sendChatCompletionRequest (request -> tools)

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)
        content = tool_result.content[0]
        print(f"    ⚙️: {content}\n")
        if isinstance(content, TextContent):
            return content.text
        else:
            return content
        # TODO:
        # 1. Call `await self.session.call_tool(tool_name, tool_args)` and assign to `tool_result: CallToolResult` variable
        # 2. Get `content` with index `0` from `tool_result` and assign to `content` variable
        # 3. print(f"    ⚙️: {content}\n")
        # 4. If `isinstance(content, TextContent)` -> return content.text
        #    else -> return content

    async def get_resources(self) -> list[Resource]:
        """Get available resources from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        try:
            response: ListResourcesResult = await self.session.list_resources()
            return response.resources
        except Exception as e:
            print(f'Error getting resources: {e}')
            return []
        # TODO:
        # Wrap into try/except (not all MCP servers have resources), get `list_resources` (it is async) and resources
        # from it. In case of error print error and return an empty array

    async def get_resource(self, uri: AnyUrl) -> str:
        """Get specific resource content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        resource: ReadResourceResult = await self.session.read_resource(uri)

        if isinstance(resource, BlobResourceContents):
            return resource.blob
        elif isinstance(resource, TextResourceContents):
            return resource.text
        return ''

    async def get_prompts(self) -> list[Prompt]:
        """Get available prompts from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        try:
            response: ListPromptsResult = await self.session.list_prompts()
            return response.prompts
        except Exception as e:
            print(f'Error getting resources: {e}')
            return []

    async def get_prompt(self, name: str) -> str:
        """Get specific prompt content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        prompt: GetPromptResult = await self.session.get_prompt(name)
        combined_content = ''

        for message in prompt.messages:
            if message.content:
                if isinstance(message.content, TextContent):
                    combined_content += message.content.text + '\n'
                if isinstance(message.content, str):
                    combined_content += message.content + '\n'
        return combined_content
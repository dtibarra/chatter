"""MCP server lifecycle management.

Manages connections to MCP servers, discovers their tools, and makes
them available to the PydanticAI agent.
"""

from __future__ import annotations

import json
import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass, field

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


@dataclass
class MCPServerInfo:
    """Runtime info about a connected MCP server."""

    name: str
    session: ClientSession
    tools: list[dict] = field(default_factory=list)


class MCPManager:
    """Manages the lifecycle of MCP server connections."""

    def __init__(self):
        self.servers: dict[str, MCPServerInfo] = {}
        self._exit_stack = AsyncExitStack()

    async def connect_stdio(
        self,
        name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> MCPServerInfo:
        """Connect to an MCP server via stdio transport."""
        params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env,
        )

        transport = await self._exit_stack.enter_async_context(
            stdio_client(params)
        )
        read_stream, write_stream = transport
        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()

        # Discover tools
        tools_response = await session.list_tools()
        tools = [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in tools_response.tools
        ]

        info = MCPServerInfo(name=name, session=session, tools=tools)
        self.servers[name] = info
        logger.info(f"Connected to MCP server '{name}' with {len(tools)} tools")
        return info

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> str:
        """Call a tool on a connected MCP server."""
        if server_name not in self.servers:
            raise ValueError(f"MCP server '{server_name}' not connected")

        server = self.servers[server_name]
        result = await server.session.call_tool(tool_name, arguments)

        # Combine text content from the result
        parts = []
        for content in result.content:
            if hasattr(content, "text"):
                parts.append(content.text)
        return "\n".join(parts)

    def get_all_tools(self) -> list[dict]:
        """Get all available tools from all connected servers."""
        all_tools = []
        for server in self.servers.values():
            for tool in server.tools:
                all_tools.append({
                    **tool,
                    "server_name": server.name,
                })
        return all_tools

    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        await self._exit_stack.aclose()
        self.servers.clear()
        logger.info("Disconnected from all MCP servers")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.disconnect_all()


# Singleton
_manager: MCPManager | None = None


def get_mcp_manager() -> MCPManager:
    global _manager
    if _manager is None:
        _manager = MCPManager()
    return _manager

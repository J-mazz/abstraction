"""
MCP Client implementation for connecting to external MCP servers.
"""
import asyncio
from typing import Any, Dict, List, Optional
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import Tool as MCPTool
from loguru import logger

from ..tools.base import BaseTool, ToolCategory, ToolOutput


class MCPClient:
    """
    MCP Client for connecting to external MCP servers and using their tools.

    This allows the Abstraction framework to discover and use tools from
    other MCP-compatible applications.
    """

    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize the MCP client.

        Args:
            server_url: URL of the MCP server to connect to (optional)
        """
        self.server_url = server_url
        self.client: Optional[ClientSession] = None
        self._connected = False
        self._available_tools: List[MCPTool] = []

    async def connect(self, command: str, args: List[str] = None):
        """
        Connect to an MCP server via stdio.

        Args:
            command: Command to run the MCP server
            args: Arguments for the command

        Example:
            await client.connect("python", ["external_mcp_server.py"])
        """
        if self._connected:
            logger.warning("MCP client is already connected")
            return

        try:
            logger.info(f"Connecting to MCP server: {command} {args or []}")

            # Connect via stdio
            async with stdio_client(command, args or []) as (read, write):
                async with ClientSession(read, write) as client:
                    self.client = client
                    self._connected = True

                    # Initialize connection
                    await client.initialize()

                    # Discover available tools
                    await self._discover_tools()

                    logger.info(f"Connected to MCP server. Found {len(self._available_tools)} tools")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self._connected = False
            raise

    async def _discover_tools(self):
        """Discover available tools from the connected server."""
        if not self.client:
            return

        try:
            tools_response = await self.client.list_tools()
            self._available_tools = tools_response.tools
            logger.info(f"Discovered {len(self._available_tools)} tools from MCP server")

        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")
            self._available_tools = []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolOutput:
        """
        Call a tool on the connected MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            ToolOutput with results
        """
        if not self._connected or not self.client:
            return ToolOutput(
                success=False,
                result=None,
                error="Not connected to MCP server"
            )

        try:
            logger.info(f"Calling MCP tool: {tool_name}")

            # Call the tool
            response = await self.client.call_tool(tool_name, arguments)

            # Extract text content from response
            result_text = ""
            for content in response.content:
                if hasattr(content, 'text'):
                    result_text += content.text

            logger.info(f"MCP tool '{tool_name}' call succeeded")

            return ToolOutput(
                success=True,
                result=result_text,
                metadata={"mcp_tool": tool_name}
            )

        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return ToolOutput(
                success=False,
                result=None,
                error=str(e)
            )

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools from the connected server.

        Returns:
            List of tool descriptions
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in self._available_tools
        ]

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if not self._connected:
            return

        logger.info("Disconnecting from MCP server...")
        self._connected = False
        self.client = None
        self._available_tools = []
        logger.info("Disconnected from MCP server")

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected


class MCPToolWrapper(BaseTool):
    """
    Wrapper to make external MCP tools compatible with Abstraction's tool system.
    """

    def __init__(self, mcp_client: MCPClient, tool_name: str, tool_description: str):
        """
        Initialize the wrapper.

        Args:
            mcp_client: Connected MCP client
            tool_name: Name of the MCP tool
            tool_description: Description of the tool
        """
        super().__init__()
        self.mcp_client = mcp_client
        self.name = f"mcp_{tool_name}"
        self.description = f"[MCP] {tool_description}"
        self._tool_name = tool_name

    @property
    def category(self) -> ToolCategory:
        """Return tool category."""
        # Default to SYSTEM for external tools
        return ToolCategory.SYSTEM

    @property
    def requires_approval(self) -> bool:
        """External tools should require approval for safety."""
        return True

    def execute(self, **kwargs) -> ToolOutput:
        """
        Execute the MCP tool.

        Args:
            **kwargs: Tool arguments

        Returns:
            ToolOutput with results
        """
        # Run async call in sync context
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a task
            return asyncio.create_task(
                self.mcp_client.call_tool(self._tool_name, kwargs)
            )
        else:
            # Otherwise run until complete
            return loop.run_until_complete(
                self.mcp_client.call_tool(self._tool_name, kwargs)
            )


async def connect_to_mcp_server(command: str, args: List[str] = None) -> MCPClient:
    """
    Helper function to connect to an MCP server.

    Args:
        command: Command to run the MCP server
        args: Arguments for the command

    Returns:
        Connected MCPClient instance
    """
    client = MCPClient()
    await client.connect(command, args)
    return client

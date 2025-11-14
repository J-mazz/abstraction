"""
MCP Server implementation for exposing Abstraction tools via Model Context Protocol.
"""
import asyncio
from typing import Any, Dict, List, Optional, Callable
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool as MCPTool, TextContent, ImageContent, EmbeddedResource
from loguru import logger

from ..tools.base import BaseTool, ToolRegistry, ToolOutput


class MCPServer:
    """
    MCP Server that exposes Abstraction tools via the Model Context Protocol.

    This allows external AI assistants and applications to discover and use
    our tools through a standardized protocol.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        name: str = "abstraction-tools",
        version: str = "1.0.0",
        host: str = "localhost",
        port: int = 3000
    ):
        """
        Initialize the MCP server.

        Args:
            tool_registry: Tool registry containing tools to expose
            name: Server name
            version: Server version
            host: Host to bind to
            port: Port to bind to
        """
        self.tool_registry = tool_registry
        self.name = name
        self.version = version
        self.host = host
        self.port = port
        self.server = Server(name)
        self._running = False
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[MCPTool]:
            """List all available tools."""
            mcp_tools = []

            for tool in self.tool_registry.get_all_tools():
                # Convert our tool to MCP tool format
                mcp_tool = MCPTool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema={
                        "type": "object",
                        "properties": self._get_tool_schema(tool),
                        "required": self._get_required_params(tool)
                    }
                )
                mcp_tools.append(mcp_tool)

            logger.info(f"MCP: Listed {len(mcp_tools)} tools")
            return mcp_tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent | EmbeddedResource]:
            """Execute a tool and return results."""
            logger.info(f"MCP: Tool call requested: {name} with args: {arguments}")

            tool = self.tool_registry.get_tool(name)
            if not tool:
                error_msg = f"Tool '{name}' not found"
                logger.error(f"MCP: {error_msg}")
                return [TextContent(type="text", text=f"Error: {error_msg}")]

            try:
                # Execute the tool
                result: ToolOutput = self.tool_registry.execute_tool(name, **arguments)

                if result.success:
                    # Format successful result
                    response_text = str(result.result)
                    if result.metadata:
                        response_text += f"\n\nMetadata: {result.metadata}"

                    logger.info(f"MCP: Tool '{name}' executed successfully")
                    return [TextContent(type="text", text=response_text)]
                else:
                    # Format error result
                    error_text = f"Tool execution failed: {result.error}"
                    logger.error(f"MCP: {error_text}")
                    return [TextContent(type="text", text=error_text)]

            except Exception as e:
                error_msg = f"Error executing tool '{name}': {str(e)}"
                logger.exception(f"MCP: {error_msg}")
                return [TextContent(type="text", text=f"Error: {error_msg}")]

    def _get_tool_schema(self, tool: BaseTool) -> Dict[str, Any]:
        """
        Generate JSON schema for tool parameters.

        Args:
            tool: Tool instance

        Returns:
            JSON schema for tool parameters
        """
        # This is a simplified schema - you may want to enhance this
        # by adding parameter type information to your BaseTool class
        return {
            "input": {
                "type": "string",
                "description": f"Input for {tool.name}"
            }
        }

    def _get_required_params(self, tool: BaseTool) -> List[str]:
        """
        Get list of required parameters for a tool.

        Args:
            tool: Tool instance

        Returns:
            List of required parameter names
        """
        # Default to no required params - enhance based on your tool definitions
        return []

    async def start(self):
        """Start the MCP server."""
        if self._running:
            logger.warning("MCP server is already running")
            return

        logger.info(f"Starting MCP server '{self.name}' v{self.version} on {self.host}:{self.port}")
        self._running = True

        # Initialize server
        async with self.server.connection():
            logger.info(f"MCP server started successfully")
            logger.info(f"Exposing {len(self.tool_registry.get_all_tools())} tools via MCP")

            # Keep server running
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                logger.info("MCP server shutdown requested")

    async def stop(self):
        """Stop the MCP server."""
        if not self._running:
            return

        logger.info("Stopping MCP server...")
        self._running = False
        logger.info("MCP server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    def get_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "name": self.name,
            "version": self.version,
            "host": self.host,
            "port": self.port,
            "running": self._running,
            "tools_count": len(self.tool_registry.get_all_tools())
        }


def create_mcp_server(
    tool_registry: ToolRegistry,
    host: str = "localhost",
    port: int = 3000
) -> MCPServer:
    """
    Factory function to create an MCP server.

    Args:
        tool_registry: Tool registry to expose
        host: Host to bind to
        port: Port to bind to

    Returns:
        Configured MCPServer instance
    """
    return MCPServer(
        tool_registry=tool_registry,
        host=host,
        port=port
    )

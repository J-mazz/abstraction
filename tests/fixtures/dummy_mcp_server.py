import anyio
from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool as MCPTool, TextContent

SERVER = Server("dummy-mcp", version="test")


@SERVER.list_tools()
async def list_tools():
    return [
        MCPTool(
            name="dummy_echo",
            description="Echo back provided text",
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": [],
            },
        )
    ]


@SERVER.call_tool()
async def call_tool(name: str, arguments: dict | None):  # pragma: no cover - exercised via integration test
    arguments = arguments or {}
    if name != "dummy_echo":
        return [TextContent(type="text", text="unknown tool")]

    payload = arguments.get("text", "")
    return [TextContent(type="text", text=f"echo:{payload}")]


async def main():  # pragma: no cover - entry point for MCP stdio
    async with stdio_server() as (read_stream, write_stream):
        init_options = SERVER.create_initialization_options(NotificationOptions())
        await SERVER.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    anyio.run(main)

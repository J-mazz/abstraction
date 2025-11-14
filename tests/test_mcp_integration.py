import sys
from pathlib import Path
from types import MethodType

import pytest
from mcp.types import Tool as MCPTool

from src.mcp.mcp_client import MCPClient, MCPToolWrapper, connect_to_mcp_server
from src.tools.base import ToolCategory, ToolOutput


@pytest.mark.asyncio
async def test_mcp_client_round_trip():
    script_path = Path(__file__).parent / "fixtures" / "dummy_mcp_server.py"
    client = MCPClient()
    await client.connect(sys.executable, [str(script_path)])

    # second connect should be a no-op when already connected
    await client.connect(sys.executable, [str(script_path)])

    result = await client.call_tool("dummy_echo", {"text": "ping"})
    assert result.success
    assert "echo:ping" in result.result

    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_client_requires_connection():
    client = MCPClient()
    result = await client.call_tool("noop", {})
    assert not result.success
    assert "not connected" in result.error.lower()


def test_mcp_client_available_tools_snapshot():
    client = MCPClient()
    client._available_tools = [
        MCPTool(name="alpha", description="demo", inputSchema={"type": "object"})
    ]

    summary = client.get_available_tools()
    assert summary[0]["name"] == "alpha"
    assert "input_schema" in summary[0]


@pytest.mark.asyncio
async def test_mcp_client_disconnect_idempotent():
    client = MCPClient()
    await client.disconnect()  # should be a no-op when not connected


@pytest.mark.asyncio
async def test_mcp_client_connect_failure_resets_state(monkeypatch):
    client = MCPClient()

    async def boom(handler):  # pylint: disable=unused-argument
        raise RuntimeError("boom")

    monkeypatch.setattr(client, "_with_client", MethodType(lambda self, handler: boom(handler), client))

    with pytest.raises(RuntimeError):
        await client.connect("python", ["-V"])

    assert client._connected is False
    assert client._command is None
    assert client._args == []


@pytest.mark.asyncio
async def test_mcp_client_with_client_requires_configuration():
    client = MCPClient()
    with pytest.raises(RuntimeError):
        await client._with_client(lambda _client: None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_mcp_client_discover_tools_handles_errors():
    class FailingClient:
        async def list_tools(self):
            raise RuntimeError("fail")

    client = MCPClient()
    await client._discover_tools(FailingClient())
    assert client._available_tools == []


@pytest.mark.asyncio
async def test_mcp_client_call_tool_reports_failure(monkeypatch):
    client = MCPClient()
    client._connected = True
    client._command = "python"

    async def boom(handler):  # pylint: disable=unused-argument
        raise RuntimeError("boom")

    monkeypatch.setattr(client, "_with_client", MethodType(lambda self, handler: boom(handler), client))

    result = await client.call_tool("noop", {})
    assert not result.success
    assert "boom" in result.error


def test_mcp_tool_wrapper_properties():
    client = MCPClient()

    async def fake_call(tool_name, kwargs):  # pylint: disable=unused-argument
        return ToolOutput(success=True, result="ok")

    client.call_tool = fake_call  # type: ignore[assignment]
    wrapper = MCPToolWrapper(client, "demo", "Demo tool")

    assert wrapper.category == ToolCategory.SYSTEM
    assert wrapper.requires_approval is True


@pytest.mark.asyncio
async def test_connect_to_mcp_server_helper():
    script_path = Path(__file__).parent / "fixtures" / "dummy_mcp_server.py"
    client = await connect_to_mcp_server(sys.executable, [str(script_path)])
    assert client.is_connected()
    await client.disconnect()


def test_mcp_tool_wrapper_executes_without_loop():
    client = MCPClient()

    async def fake_call(tool_name, kwargs):  # pylint: disable=unused-argument
        return ToolOutput(success=True, result=kwargs.get("text", ""))

    client.call_tool = fake_call  # type: ignore[assignment]

    wrapper = MCPToolWrapper(client, "echo", "Echo tool")
    result = wrapper.execute(text="ping")
    assert result.success
    assert result.result == "ping"


@pytest.mark.asyncio
async def test_mcp_tool_wrapper_handles_running_loop():
    client = MCPClient()

    async def fake_call(tool_name, kwargs):  # pylint: disable=unused-argument
        return ToolOutput(success=True, result="loop")

    client.call_tool = fake_call  # type: ignore[assignment]

    wrapper = MCPToolWrapper(client, "loop", "Loop tool")
    # Call directly while the event loop is running to exercise the thread executor code path
    result = wrapper.execute()
    assert result.result == "loop"

from contextlib import asynccontextmanager
from types import MethodType

import pytest

from mcp import types

from src.mcp.mcp_server import MCPServer
from src.tools.base import BaseTool, ToolCategory, ToolOutput, ToolRegistry


class UpperTool(BaseTool):
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WRITING

    @property
    def requires_approval(self) -> bool:
        return False

    def execute(self, text: str):
        return ToolOutput(success=True, result=text.upper())


class MetadataTool(BaseTool):
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WRITING

    @property
    def requires_approval(self) -> bool:
        return False

    def execute(self, text: str):
        return ToolOutput(success=True, result=text.upper(), metadata={"origin": "meta"})


@pytest.fixture
def server():
    registry = ToolRegistry()
    registry.register(UpperTool())
    return MCPServer(tool_registry=registry)


@pytest.fixture
def metadata_server():
    registry = ToolRegistry()
    registry.register(MetadataTool())
    return MCPServer(tool_registry=registry)


@pytest.mark.anyio
async def test_mcp_server_lists_tools(server):
    handler = server.server.request_handlers[types.ListToolsRequest]
    request = types.ListToolsRequest(params=None)
    response = await handler(request)
    assert "UpperTool" in response.root.tools[0].name


@pytest.mark.anyio
async def test_mcp_server_executes_tool(server):
    handler = server.server.request_handlers[types.CallToolRequest]
    params = types.CallToolRequestParams(name="UpperTool", arguments={"text": "ping"})
    request = types.CallToolRequest(params=params)
    result = await handler(request)
    content = result.root.content[0]
    assert content.text.startswith("PING")


@pytest.mark.anyio
async def test_mcp_server_missing_tool_returns_error(server):
    handler = server.server.request_handlers[types.CallToolRequest]
    params = types.CallToolRequestParams(name="MissingTool", arguments={})
    request = types.CallToolRequest(params=params)
    response = await handler(request)
    assert response.root.isError is True
    assert "not found" in response.root.content[0].text.lower()


@pytest.mark.anyio
async def test_mcp_server_includes_metadata(metadata_server):
    handler = metadata_server.server.request_handlers[types.CallToolRequest]
    params = types.CallToolRequestParams(name="MetadataTool", arguments={"text": "hey"})
    request = types.CallToolRequest(params=params)
    response = await handler(request)
    assert "Metadata:" in response.root.content[0].text


@pytest.mark.anyio
async def test_mcp_server_handles_execution_error(server, monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(server.tool_registry, "execute_tool", boom)

    handler = server.server.request_handlers[types.CallToolRequest]
    params = types.CallToolRequestParams(name="UpperTool", arguments={"text": "ping"})
    request = types.CallToolRequest(params=params)
    response = await handler(request)
    assert response.root.isError is True
    assert "error executing" in response.root.content[0].text.lower()


def test_mcp_server_info_and_schema(server):
    info = server.get_info()
    assert info["name"] == server.name
    assert info["tools_count"] == 1
    assert server.is_running() is False

    schema = server._get_tool_schema(UpperTool())  # pylint: disable=protected-access
    assert schema["input"]["type"] == "string"
    assert server._get_required_params(UpperTool()) == []  # pylint: disable=protected-access


@pytest.mark.anyio
async def test_mcp_server_stop_updates_state(server):
    server._running = True  # pylint: disable=protected-access
    await server.stop()
    assert server.is_running() is False


@pytest.mark.anyio
async def test_mcp_server_start_is_idempotent(server):
    server._running = True  # pylint: disable=protected-access
    await server.start()


@pytest.mark.anyio
async def test_mcp_server_start_enters_connection(server, monkeypatch):
    call_state = {"entered": False, "run": False}

    @asynccontextmanager
    async def fake_connection():
        call_state["entered"] = True
        yield (None, None)

    async def fake_run(self, read_stream, write_stream, init_options, **kwargs):  # pylint: disable=unused-argument
        call_state["run"] = True

    monkeypatch.setattr("src.mcp.mcp_server.stdio_server", lambda: fake_connection())
    monkeypatch.setattr(server.server, "run", MethodType(fake_run, server.server))

    await server.start()
    assert call_state["entered"] is True
    assert call_state["run"] is True
    assert server.is_running() is False

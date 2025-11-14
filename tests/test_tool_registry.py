import pytest

from src.tools.base import BaseTool, ToolCategory, ToolOutput, ToolRegistry


class DummyFirewall:
    def __init__(self, allow=True):
        self.allow = allow
        self.filtered = False

    def validate_tool_execution(self, name, kwargs):
        if self.allow:
            return True, None
        return False, "blocked"

    def filter_output(self, output):
        self.filtered = True
        return output


class EchoTool(BaseTool):
    @property
    def category(self):
        return ToolCategory.WRITING

    @property
    def requires_approval(self):
        return False

    def execute(self, text: str):
        return ToolOutput(success=True, result=text.upper())


@pytest.fixture
def registry(monkeypatch):
    reg = ToolRegistry()
    fake_firewall = DummyFirewall()
    monkeypatch.setattr("src.tools.base.io_firewall", fake_firewall)
    reg.register(EchoTool())
    return reg


def test_registry_lists_tools(registry):
    listing = registry.list_tools()
    assert "writing" in listing
    assert "EchoTool" in listing["writing"]


def test_registry_executes_tools(monkeypatch):
    reg = ToolRegistry()
    firewall = DummyFirewall()
    monkeypatch.setattr("src.tools.base.io_firewall", firewall)
    reg.register(EchoTool())

    result = reg.execute_tool("EchoTool", text="loud")
    assert result.success
    assert result.result == "LOUD"
    assert firewall.filtered is True


def test_registry_handles_missing_tool(registry):
    response = registry.execute_tool("MissingTool")
    assert not response.success
    assert "not found" in response.error


def test_registry_blocks_by_firewall(monkeypatch):
    reg = ToolRegistry()
    firewall = DummyFirewall(allow=False)
    monkeypatch.setattr("src.tools.base.io_firewall", firewall)
    reg.register(EchoTool())

    result = reg.execute_tool("EchoTool", text="test")
    assert not result.success
    assert "Security" in result.error

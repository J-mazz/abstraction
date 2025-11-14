import pytest

from src.tools import register_all_tools
from src.tools.base import ToolCategory, ToolRegistry


@pytest.fixture
def fresh_registry(monkeypatch):
    registry = ToolRegistry()
    monkeypatch.setattr("src.tools.tool_registry", registry)
    return registry


def test_register_all_tools_applies_web_config(fresh_registry):
    config = {"tools": {"web": {"allowed_hosts": ["example.com", "*.trusted.com"], "timeout": 12}}}

    register_all_tools(config)

    web_tools = fresh_registry.get_tools_by_category(ToolCategory.WEB)
    assert len(web_tools) == 3

    http_tool = next(tool for tool in web_tools if tool.__class__.__name__ == "HTTPRequestTool")
    assert "example.com" in http_tool._allowed_hosts  # pylint: disable=protected-access
    assert "*.trusted.com" in http_tool._allowed_hosts  # pylint: disable=protected-access
    assert getattr(http_tool, "_timeout", None) == 12


def test_register_all_tools_registers_all_categories(fresh_registry):
    register_all_tools()

    categories = fresh_registry.list_tools()
    assert set(categories.keys()) == {
        "coding",
        "web",
        "accounting",
        "writing",
    }

    assert len(fresh_registry.get_all_tools()) == 15

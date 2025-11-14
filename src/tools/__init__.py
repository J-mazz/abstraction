"""Tool system for the agent."""
from typing import Any, Dict, Optional

from .base import (
    BaseTool,
    ToolCategory,
    ToolInput,
    ToolOutput,
    ToolRegistry,
    tool_registry
)
from .coding_tools import (
    CodeFormatterTool,
    CodeLinterTool,
    CodeExecutorTool,
    FileReadTool,
    FileWriteTool
)
from .web_tools import (
    WebScraperTool,
    HTTPRequestTool,
    URLValidatorTool
)
from .accounting_tools import (
    CalculatorTool,
    SpreadsheetReaderTool,
    InvoiceCalculatorTool
)
from .writing_tools import (
    WordCounterTool,
    TextSummarizerTool,
    GrammarCheckerTool,
    TextFormatterTool
)


def _get_tool_config(config: Optional[Dict[str, Any]], *keys, default=None):
    current = config or {}
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def register_all_tools(config: Optional[Dict[str, Any]] = None):
    """Register all available tools."""
    web_config = _get_tool_config(config, 'tools', 'web', default={}) or {}
    web_allowed_hosts = web_config.get('allowed_hosts') or []
    web_timeout = web_config.get('timeout', 30)
    # Coding tools
    tool_registry.register(CodeFormatterTool())
    tool_registry.register(CodeLinterTool())
    tool_registry.register(CodeExecutorTool())
    tool_registry.register(FileReadTool())
    tool_registry.register(FileWriteTool())

    # Web tools
    tool_registry.register(WebScraperTool(allowed_hosts=web_allowed_hosts, timeout=web_timeout))
    tool_registry.register(HTTPRequestTool(allowed_hosts=web_allowed_hosts, timeout=web_timeout))
    tool_registry.register(URLValidatorTool())

    # Accounting tools
    tool_registry.register(CalculatorTool())
    tool_registry.register(SpreadsheetReaderTool())
    tool_registry.register(InvoiceCalculatorTool())

    # Writing tools
    tool_registry.register(WordCounterTool())
    tool_registry.register(TextSummarizerTool())
    tool_registry.register(GrammarCheckerTool())
    tool_registry.register(TextFormatterTool())


__all__ = [
    'BaseTool',
    'ToolCategory',
    'ToolInput',
    'ToolOutput',
    'ToolRegistry',
    'tool_registry',
    'register_all_tools',
]

"""Tool system for the agent."""
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


def register_all_tools():
    """Register all available tools."""
    # Coding tools
    tool_registry.register(CodeFormatterTool())
    tool_registry.register(CodeLinterTool())
    tool_registry.register(CodeExecutorTool())
    tool_registry.register(FileReadTool())
    tool_registry.register(FileWriteTool())

    # Web tools
    tool_registry.register(WebScraperTool())
    tool_registry.register(HTTPRequestTool())
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

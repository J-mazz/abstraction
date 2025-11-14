"""
Base tool class and tool registry for the agent system.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from enum import Enum
from loguru import logger


class ToolCategory(str, Enum):
    """Tool categories for organization."""
    CODING = "coding"
    WEB = "web"
    ACCOUNTING = "accounting"
    WRITING = "writing"
    FILE_OPS = "file_operations"
    SYSTEM = "system"
    DATA_ANALYSIS = "data_analysis"


class ToolInput(BaseModel):
    """Base class for tool inputs."""
    pass


class ToolOutput(BaseModel):
    """Base class for tool outputs."""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Base class for all tools."""

    def __init__(self):
        """Initialize the tool."""
        self.name = self.__class__.__name__
        self.description = self.__doc__ or "No description provided"

    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Return the tool category."""
        pass

    @property
    def requires_approval(self) -> bool:
        """Whether this tool requires human approval before execution."""
        return True  # Default to requiring approval for safety

    @abstractmethod
    def execute(self, **kwargs) -> ToolOutput:
        """
        Execute the tool.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            ToolOutput with results
        """
        pass

    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            True if valid, False otherwise
        """
        return True

    def to_langchain_tool(self) -> Dict[str, Any]:
        """
        Convert to LangChain tool format.

        Returns:
            Dictionary representing the tool for LangChain
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "requires_approval": self.requires_approval
        }


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._tools_by_category: Dict[ToolCategory, List[BaseTool]] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool

        # Add to category index
        if tool.category not in self._tools_by_category:
            self._tools_by_category[tool.category] = []
        self._tools_by_category[tool.category].append(tool)

        logger.info(f"Registered tool: {tool.name} ({tool.category.value})")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def get_tools_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """
        Get all tools in a category.

        Args:
            category: Tool category

        Returns:
            List of tools in the category
        """
        return self._tools_by_category.get(category, [])

    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools.

        Returns:
            List of all tools
        """
        return list(self._tools.values())

    def list_tools(self) -> Dict[str, List[str]]:
        """
        List all tools grouped by category.

        Returns:
            Dictionary mapping category to tool names
        """
        result = {}
        for category, tools in self._tools_by_category.items():
            result[category.value] = [tool.name for tool in tools]
        return result

    def execute_tool(self, name: str, use_firewall: bool = True, **kwargs) -> ToolOutput:
        """
        Execute a tool by name with optional firewall protection.

        Args:
            name: Tool name
            use_firewall: Whether to use I/O firewall (default True)
            **kwargs: Tool arguments

        Returns:
            ToolOutput with results
        """
        tool = self.get_tool(name)
        if not tool:
            return ToolOutput(
                success=False,
                result=None,
                error=f"Tool '{name}' not found"
            )

        try:
            # Firewall validation (if enabled)
            if use_firewall:
                try:
                    from ..mcp.firewall import io_firewall
                    is_valid, error_msg = io_firewall.validate_tool_execution(name, kwargs)
                    if not is_valid:
                        logger.warning(f"Firewall blocked tool '{name}': {error_msg}")
                        return ToolOutput(
                            success=False,
                            result=None,
                            error=f"Security validation failed: {error_msg}"
                        )
                except ImportError:
                    logger.warning("Firewall module not available, skipping validation")

            # Tool input validation
            if not tool.validate_input(**kwargs):
                return ToolOutput(
                    success=False,
                    result=None,
                    error=f"Invalid input for tool '{name}'"
                )

            # Execute tool
            result = tool.execute(**kwargs)

            # Filter output through firewall (if enabled)
            if use_firewall and result.success:
                try:
                    from ..mcp.firewall import io_firewall
                    result.result = io_firewall.filter_output(result.result)
                except ImportError:
                    pass

            return result

        except Exception as e:
            logger.error(f"Tool '{name}' execution failed: {e}")
            return ToolOutput(
                success=False,
                result=None,
                error=str(e)
            )


# Global tool registry instance
tool_registry = ToolRegistry()

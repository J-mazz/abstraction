"""
Tools for coding tasks.
"""
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import black
import autopep8
from .base import BaseTool, ToolCategory, ToolOutput


class CodeFormatterTool(BaseTool):
    """Format Python code using Black."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CODING

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only operation

    def execute(self, code: str, line_length: int = 88) -> ToolOutput:
        """
        Format Python code.

        Args:
            code: Python code to format
            line_length: Maximum line length

        Returns:
            ToolOutput with formatted code
        """
        try:
            formatted = black.format_str(code, mode=black.Mode(line_length=line_length))
            return ToolOutput(
                success=True,
                result=formatted,
                metadata={"formatter": "black", "line_length": line_length}
            )
        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))


class CodeLinterTool(BaseTool):
    """Run pylint on Python code."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CODING

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only operation

    def execute(self, code: str, file_path: Optional[str] = None) -> ToolOutput:
        """
        Lint Python code.

        Args:
            code: Python code to lint
            file_path: Optional file path for context

        Returns:
            ToolOutput with lint results
        """
        temp_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_path = Path(temp_file.name)

            # Run pylint
            result = subprocess.run(
                ["pylint", str(temp_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            return ToolOutput(
                success=True,
                result={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                },
                metadata={"linter": "pylint"}
            )
        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()


class CodeExecutorTool(BaseTool):
    """Execute Python code in a sandboxed environment."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CODING

    @property
    def requires_approval(self) -> bool:
        return True  # Requires approval for safety

    def execute(self, code: str, timeout: int = 30) -> ToolOutput:
        """
        Execute Python code.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds

        Returns:
            ToolOutput with execution results
        """
        temp_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_path = Path(temp_file.name)

            # Execute
            result = subprocess.run(
                ["python3", str(temp_path)],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return ToolOutput(
                success=result.returncode == 0,
                result={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                },
                metadata={"timeout": timeout}
            )
        except subprocess.TimeoutExpired:
            return ToolOutput(
                success=False,
                result=None,
                error=f"Execution timed out after {timeout} seconds"
            )
        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()


class FileReadTool(BaseTool):
    """Read file contents."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CODING

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only operation

    def execute(self, file_path: str, encoding: str = "utf-8") -> ToolOutput:
        """
        Read file contents.

        Args:
            file_path: Path to the file
            encoding: File encoding

        Returns:
            ToolOutput with file contents
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolOutput(
                    success=False,
                    result=None,
                    error=f"File not found: {file_path}"
                )

            content = path.read_text(encoding=encoding)
            return ToolOutput(
                success=True,
                result=content,
                metadata={
                    "file_path": file_path,
                    "size": len(content),
                    "encoding": encoding
                }
            )
        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))


class FileWriteTool(BaseTool):
    """Write content to a file."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CODING

    @property
    def requires_approval(self) -> bool:
        return True  # Write operation requires approval

    def execute(self, file_path: str, content: str, encoding: str = "utf-8") -> ToolOutput:
        """
        Write content to a file.

        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding

        Returns:
            ToolOutput with success status
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)

            return ToolOutput(
                success=True,
                result=f"Successfully wrote {len(content)} characters to {file_path}",
                metadata={
                    "file_path": file_path,
                    "size": len(content),
                    "encoding": encoding
                }
            )
        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))

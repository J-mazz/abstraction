"""
I/O Firewall for input/output validation and sandboxing.

Provides security layers for tool execution including:
- Input validation and sanitization
- Output filtering
- Resource limits
- Path traversal prevention
- Code injection prevention
"""
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from loguru import logger
from pydantic import BaseModel, Field, validator


class FirewallRule(BaseModel):
    """A firewall rule for input/output validation."""
    name: str
    description: str
    enabled: bool = True
    severity: str = "high"  # low, medium, high, critical


class IOFirewall:
    """
    I/O Firewall for securing tool execution.

    Provides multiple layers of security:
    1. Input validation - Sanitize and validate inputs
    2. Path security - Prevent path traversal attacks
    3. Code injection prevention - Block malicious code patterns
    4. Resource limits - Limit file sizes, execution time, etc.
    5. Output filtering - Remove sensitive data from outputs
    """

    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = [
        r'(__import__|exec|eval|compile)\s*\(',  # Python execution
        r'\$\(.*\)',  # Shell command substitution
        r'`.*`',  # Backtick command execution
        r';\s*rm\s+-rf',  # Destructive commands
        r'\|\s*sh',  # Pipe to shell
        r'>\s*/dev/',  # Writing to device files
        r'<\s*script',  # Script injection (case insensitive)
    ]

    # Sensitive data patterns to filter from outputs
    SENSITIVE_PATTERNS = [
        r'(?i)(password|passwd|pwd)\s*[:=]\s*[^\s]+',  # Passwords
        r'(?i)(api[_-]?key|apikey)\s*[:=]\s*[^\s]+',  # API keys
        r'(?i)(secret|token)\s*[:=]\s*[^\s]+',  # Secrets/tokens
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses (optional)
    ]

    def __init__(
        self,
        enabled: bool = True,
        allowed_paths: Optional[List[str]] = None,
        blocked_extensions: Optional[Set[str]] = None,
        max_file_size_mb: float = 100.0,
        max_output_length: int = 1_000_000,
        filter_sensitive: bool = True
    ):
        """
        Initialize the firewall.

        Args:
            enabled: Whether firewall is enabled
            allowed_paths: List of allowed base paths (defaults to current directory)
            blocked_extensions: File extensions to block (defaults to executables)
            max_file_size_mb: Maximum file size in MB
            max_output_length: Maximum output length in characters
            filter_sensitive: Whether to filter sensitive data from outputs
        """
        self.enabled = enabled
        self.allowed_paths = allowed_paths or [os.getcwd()]
        self.blocked_extensions = blocked_extensions or {
            '.exe', '.dll', '.so', '.dylib', '.sh', '.bat', '.cmd', '.ps1'
        }
        self.max_file_size_mb = max_file_size_mb
        self.max_output_length = max_output_length
        self.filter_sensitive = filter_sensitive

        # Compile regex patterns
        self._dangerous_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]
        self._sensitive_regex = [re.compile(pattern) for pattern in self.SENSITIVE_PATTERNS]

        logger.info(f"I/O Firewall initialized (enabled={enabled})")

    def validate_input(self, input_data: Any, context: str = "general") -> tuple[bool, Optional[str]]:
        """
        Validate input data for security issues.

        Args:
            input_data: Input data to validate
            context: Context of the input (e.g., "file_path", "code", "text")

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.enabled:
            return True, None

        # Convert to string for pattern matching
        input_str = str(input_data)

        # Check for dangerous patterns
        for pattern in self._dangerous_regex:
            if pattern.search(input_str):
                error_msg = f"Blocked dangerous pattern in input: {pattern.pattern}"
                logger.warning(f"Firewall: {error_msg}")
                return False, error_msg

        # Context-specific validation
        if context == "file_path":
            is_valid, error = self.validate_file_path(input_data)
            if not is_valid:
                return False, error

        elif context == "code":
            # Additional code validation
            if any(keyword in input_str.lower() for keyword in ['system', 'popen', 'subprocess']):
                logger.warning("Firewall: Blocked potentially dangerous system call in code")
                return False, "Code contains potentially dangerous system calls"

        # Check input length
        if len(input_str) > self.max_output_length:
            return False, f"Input exceeds maximum length of {self.max_output_length} characters"

        return True, None

    def validate_file_path(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate file path for security issues.

        Args:
            file_path: Path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.enabled:
            return True, None

        try:
            # Resolve path and check for traversal
            resolved_path = Path(file_path).resolve()

            # Check if path is within allowed directories
            is_allowed = any(
                resolved_path.is_relative_to(Path(allowed).resolve())
                for allowed in self.allowed_paths
            )

            if not is_allowed:
                error_msg = f"Path '{file_path}' is outside allowed directories"
                logger.warning(f"Firewall: {error_msg}")
                return False, error_msg

            # Check file extension
            if resolved_path.suffix.lower() in self.blocked_extensions:
                error_msg = f"File extension '{resolved_path.suffix}' is blocked"
                logger.warning(f"Firewall: {error_msg}")
                return False, error_msg

            # Check file size if file exists
            if resolved_path.exists() and resolved_path.is_file():
                size_mb = resolved_path.stat().st_size / (1024 * 1024)
                if size_mb > self.max_file_size_mb:
                    error_msg = f"File size ({size_mb:.2f}MB) exceeds limit ({self.max_file_size_mb}MB)"
                    logger.warning(f"Firewall: {error_msg}")
                    return False, error_msg

            return True, None

        except Exception as e:
            error_msg = f"Invalid file path: {str(e)}"
            logger.error(f"Firewall: {error_msg}")
            return False, error_msg

    def filter_output(self, output: Any) -> Any:
        """
        Filter output to remove sensitive information.

        Args:
            output: Output data to filter

        Returns:
            Filtered output
        """
        if not self.enabled or not self.filter_sensitive:
            return output

        output_str = str(output)

        # Replace sensitive patterns
        for pattern in self._sensitive_regex:
            matches = pattern.finditer(output_str)
            for match in matches:
                # Replace matched text with asterisks
                matched_text = match.group(0)
                replacement = '[REDACTED]'
                output_str = output_str.replace(matched_text, replacement)
                logger.info(f"Firewall: Filtered sensitive data from output")

        # Truncate if too long
        if len(output_str) > self.max_output_length:
            output_str = output_str[:self.max_output_length] + "\n... (output truncated)"
            logger.info(f"Firewall: Truncated output to {self.max_output_length} characters")

        return output_str

    def validate_tool_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate tool execution before it runs.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.enabled:
            return True, None

        logger.debug(f"Firewall: Validating tool execution - {tool_name}")

        # Validate all arguments
        for arg_name, arg_value in arguments.items():
            # Determine context based on argument name
            context = "general"
            if 'path' in arg_name.lower() or 'file' in arg_name.lower():
                context = "file_path"
            elif 'code' in arg_name.lower() or 'script' in arg_name.lower():
                context = "code"

            is_valid, error = self.validate_input(arg_value, context=context)
            if not is_valid:
                return False, f"Argument '{arg_name}': {error}"

        return True, None

    def get_status(self) -> Dict[str, Any]:
        """
        Get firewall status and configuration.

        Returns:
            Dictionary with firewall status
        """
        return {
            "enabled": self.enabled,
            "allowed_paths": self.allowed_paths,
            "blocked_extensions": list(self.blocked_extensions),
            "max_file_size_mb": self.max_file_size_mb,
            "max_output_length": self.max_output_length,
            "filter_sensitive": self.filter_sensitive,
            "rules_count": {
                "dangerous_patterns": len(self._dangerous_regex),
                "sensitive_patterns": len(self._sensitive_regex)
            }
        }


# Global firewall instance
io_firewall = IOFirewall()


def validate_input(input_data: Any, context: str = "general") -> tuple[bool, Optional[str]]:
    """
    Convenience function for input validation.

    Args:
        input_data: Input to validate
        context: Validation context

    Returns:
        Tuple of (is_valid, error_message)
    """
    return io_firewall.validate_input(input_data, context)


def filter_output(output: Any) -> Any:
    """
    Convenience function for output filtering.

    Args:
        output: Output to filter

    Returns:
        Filtered output
    """
    return io_firewall.filter_output(output)

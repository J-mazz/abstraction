#!/usr/bin/env python3
"""
Test script for MCP integration and firewall functionality.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools import register_all_tools, tool_registry
from src.mcp.firewall import io_firewall, validate_input, filter_output
from loguru import logger

logger.add(sys.stdout, level="INFO")


def test_firewall():
    """Test firewall functionality."""
    print("\n" + "="*60)
    print("Testing I/O Firewall")
    print("="*60)

    # Test 1: Valid input
    print("\n1. Testing valid input...")
    is_valid, error = validate_input("Hello, world!", context="general")
    print(f"   Valid input: {is_valid}, Error: {error}")
    assert is_valid, "Valid input should pass"

    # Test 2: Dangerous pattern detection
    print("\n2. Testing dangerous pattern detection...")
    is_valid, error = validate_input("exec('malicious code')", context="code")
    print(f"   Dangerous code: {is_valid}, Error: {error}")
    assert not is_valid, "Dangerous code should be blocked"

    # Test 3: Path validation
    print("\n3. Testing path validation...")
    is_valid, error = validate_input("../../etc/passwd", context="file_path")
    print(f"   Path traversal: {is_valid}, Error: {error}")
    # May or may not be valid depending on current directory

    # Test 4: Sensitive data filtering
    print("\n4. Testing sensitive data filtering...")
    output = "User password: secret123 and api_key: abc123xyz"
    filtered = filter_output(output)
    print(f"   Original: {output}")
    print(f"   Filtered: {filtered}")
    assert "secret123" not in str(filtered), "Password should be filtered"

    print("\n✓ Firewall tests passed!")


def test_tool_execution_with_firewall():
    """Test tool execution with firewall protection."""
    print("\n" + "="*60)
    print("Testing Tool Execution with Firewall")
    print("="*60)

    # Register tools
    register_all_tools()

    # Test 1: Execute a safe tool
    print("\n1. Testing safe tool execution...")
    result = tool_registry.execute_tool(
        "WordCounterTool",
        text="Hello world! This is a test."
    )
    print(f"   Success: {result.success}")
    print(f"   Result: {result.result}")
    assert result.success, "Tool execution should succeed"

    # Test 2: Try to execute with malicious input (should be blocked)
    print("\n2. Testing malicious input blocking...")
    result = tool_registry.execute_tool(
        "CodeExecutorTool",
        code="exec('import os; os.system(\"rm -rf /\")')"
    )
    print(f"   Success: {result.success}")
    print(f"   Error: {result.error}")
    # Should be blocked by firewall
    assert not result.success, "Malicious code should be blocked"

    print("\n✓ Tool execution tests passed!")


def test_firewall_status():
    """Test firewall status retrieval."""
    print("\n" + "="*60)
    print("Firewall Status")
    print("="*60)

    status = io_firewall.get_status()
    print(f"\nEnabled: {status['enabled']}")
    print(f"Allowed paths: {status['allowed_paths']}")
    print(f"Blocked extensions: {status['blocked_extensions']}")
    print(f"Max file size: {status['max_file_size_mb']}MB")
    print(f"Filter sensitive: {status['filter_sensitive']}")
    print(f"Dangerous patterns: {status['rules_count']['dangerous_patterns']}")
    print(f"Sensitive patterns: {status['rules_count']['sensitive_patterns']}")


def main():
    """Run all tests."""
    try:
        print("\n" + "="*60)
        print("MCP Integration Test Suite")
        print("="*60)

        # Test firewall
        test_firewall()

        # Test tool execution with firewall
        test_tool_execution_with_firewall()

        # Show firewall status
        test_firewall_status()

        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

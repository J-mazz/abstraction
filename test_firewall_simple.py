#!/usr/bin/env python3
"""
Simple test for firewall functionality (no external dependencies).
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp.firewall import IOFirewall


def test_firewall():
    """Test firewall functionality."""
    print("\n" + "="*60)
    print("Testing I/O Firewall")
    print("="*60)

    # Create firewall instance
    firewall = IOFirewall(enabled=True)

    # Test 1: Valid input
    print("\n1. Testing valid input...")
    is_valid, error = firewall.validate_input("Hello, world!", context="general")
    print(f"   Valid input: {is_valid}, Error: {error}")
    assert is_valid, "Valid input should pass"

    # Test 2: Dangerous pattern detection
    print("\n2. Testing dangerous pattern detection...")
    is_valid, error = firewall.validate_input("exec('malicious code')", context="code")
    print(f"   Dangerous code detected: {is_valid}, Error: {error}")
    assert not is_valid, "Dangerous code should be blocked"

    # Test 3: Shell command injection
    print("\n3. Testing shell command injection...")
    is_valid, error = firewall.validate_input("$(rm -rf /)", context="general")
    print(f"   Shell injection blocked: {is_valid}, Error: {error}")
    assert not is_valid, "Shell injection should be blocked"

    # Test 4: Sensitive data filtering
    print("\n4. Testing sensitive data filtering...")
    output = "User password: secret123 and api_key: abc123xyz"
    filtered = firewall.filter_output(output)
    print(f"   Original: {output}")
    print(f"   Filtered: {filtered}")
    assert "secret123" not in str(filtered), "Password should be filtered"

    # Test 5: Path validation
    print("\n5. Testing path validation...")
    firewall.allowed_paths = [str(Path.cwd())]
    is_valid, error = firewall.validate_file_path("./test.txt")
    print(f"   Valid path: {is_valid}, Error: {error}")
    assert is_valid, "Path in allowed directory should be valid"

    # Test 6: Path traversal detection
    print("\n6. Testing path traversal detection...")
    is_valid, error = firewall.validate_file_path("../../etc/passwd")
    print(f"   Path traversal blocked: {is_valid}, Error: {error}")
    # Should be blocked (outside allowed path)

    # Test 7: Blocked extensions
    print("\n7. Testing blocked file extensions...")
    is_valid, error = firewall.validate_file_path("./malware.exe")
    print(f"   Executable blocked: {is_valid}, Error: {error}")
    assert not is_valid, "Executable files should be blocked"

    # Test 8: Tool execution validation
    print("\n8. Testing tool execution validation...")
    is_valid, error = firewall.validate_tool_execution(
        "TestTool",
        {"code": "print('hello')", "file_path": "./test.txt"}
    )
    print(f"   Tool execution valid: {is_valid}, Error: {error}")

    # Test 9: Firewall status
    print("\n9. Getting firewall status...")
    status = firewall.get_status()
    print(f"   Enabled: {status['enabled']}")
    print(f"   Max file size: {status['max_file_size_mb']}MB")
    print(f"   Filter sensitive: {status['filter_sensitive']}")
    print(f"   Dangerous patterns: {status['rules_count']['dangerous_patterns']}")
    print(f"   Sensitive patterns: {status['rules_count']['sensitive_patterns']}")

    print("\n✓ All firewall tests passed!")


def main():
    """Run all tests."""
    try:
        print("\n" + "="*60)
        print("Firewall Test Suite")
        print("="*60)

        test_firewall()

        print("\n" + "="*60)
        print("✓ All tests completed successfully!")
        print("="*60)

    except AssertionError as e:
        print(f"\n✗ Test assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

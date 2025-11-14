import pytest

from src.mcp.firewall import IOFirewall, filter_output, validate_input


@pytest.fixture
def firewall(tmp_path):
    return IOFirewall(
        enabled=True,
        allowed_paths=[str(tmp_path)],
        max_file_size_mb=1.0,
        filter_sensitive=True,
    )


def test_firewall_accepts_harmless_input(firewall):
    is_valid, error = firewall.validate_input("Hello, world!", context="general")
    assert is_valid
    assert error is None


def test_firewall_blocks_dangerous_code(firewall):
    is_valid, error = firewall.validate_input("exec('rm -rf /')", context="code")
    assert not is_valid
    assert "dangerous" in error.lower()


def test_firewall_blocks_suspicious_code_keywords(firewall):
    is_valid, error = firewall.validate_input("please call subprocess module", context="code")
    assert not is_valid
    assert "system" in error.lower()


def test_firewall_filters_sensitive_output(firewall):
    raw_output = "user password: secret123 and api_key: deadbeef"
    filtered = firewall.filter_output(raw_output)
    assert "secret123" not in filtered
    assert "deadbeef" not in filtered


def test_firewall_validates_file_paths(tmp_path):
    allowed_firewall = IOFirewall(enabled=True, allowed_paths=[str(tmp_path)])
    safe_file = tmp_path / "notes.txt"
    safe_file.write_text("data")

    is_valid, error = allowed_firewall.validate_file_path(str(safe_file))
    assert is_valid and error is None

    is_valid, error = allowed_firewall.validate_file_path("/etc/passwd")
    assert not is_valid
    assert "outside" in error.lower()


def test_firewall_tool_execution_validation():
    firewall = IOFirewall(enabled=True)
    is_valid, error = firewall.validate_tool_execution(
        "CodeExecutorTool",
        {"code": "$(rm -rf /)", "text": "harmless"},
    )
    assert not is_valid
    assert "dangerous" in error.lower()


def test_firewall_disabled_allows_everything():
    firewall = IOFirewall(enabled=False)
    is_valid, error = firewall.validate_input("whatever", context="code")
    assert is_valid and error is None


def test_firewall_blocks_extensions(tmp_path):
    firewall = IOFirewall(enabled=True, allowed_paths=[str(tmp_path)])
    exe_path = tmp_path / "run.exe"
    exe_path.write_text("bin")
    is_valid, error = firewall.validate_file_path(str(exe_path))
    assert not is_valid
    assert "extension" in error.lower()


def test_firewall_rejects_large_files(tmp_path):
    firewall = IOFirewall(enabled=True, allowed_paths=[str(tmp_path)], max_file_size_mb=0.0001)
    large_file = tmp_path / "big.txt"
    large_file.write_bytes(b"x" * 2048)
    is_valid, error = firewall.validate_file_path(str(large_file))
    assert not is_valid
    assert "exceeds" in error.lower()


def test_firewall_truncates_long_output():
    firewall = IOFirewall(enabled=True, max_output_length=10)
    filtered = firewall.filter_output("0123456789ABCDEFG")
    assert filtered.endswith("(output truncated)")


def test_firewall_rejects_oversized_input():
    firewall = IOFirewall(enabled=True, max_output_length=5)
    is_valid, error = firewall.validate_input("toolongvalue", context="general")
    assert not is_valid
    assert "exceeds" in error.lower()


def test_firewall_status_reports_configuration(firewall):
    status = firewall.get_status()
    assert status["allowed_paths"]
    assert status["rules_count"]["dangerous_patterns"] >= 1


def test_firewall_helpers_use_global_instance():
    ok, error = validate_input("hello world")
    assert ok and error is None

    masked = filter_output("password: abc123")
    assert "[REDACTED]" in masked


def test_firewall_tool_validation_detects_bad_paths(tmp_path):
    firewall = IOFirewall(enabled=True, allowed_paths=[str(tmp_path)])
    is_valid, error = firewall.validate_tool_execution(
        "FileTool",
        {"file_path": "/etc/passwd", "text": "ok"},
    )
    assert not is_valid
    assert "outside" in error.lower()

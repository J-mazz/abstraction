from pathlib import Path

import pytest

from src.tools import (
    ToolRegistry,
    WordCounterTool,
    FileWriteTool,
    FileReadTool,
    CalculatorTool,
)


@pytest.fixture
def registry():
    reg = ToolRegistry()
    reg.register(WordCounterTool())
    reg.register(FileWriteTool())
    reg.register(FileReadTool())
    reg.register(CalculatorTool())
    return reg


def test_word_counter_counts_words(registry):
    result = registry.execute_tool(
        "WordCounterTool",
        use_firewall=False,
        text="Hello world! This is a test.",
    )
    assert result.success
    assert result.result["word_count"] == 6


def test_file_read_write_roundtrip(tmp_path, registry):
    target = tmp_path / "sample.txt"
    write_result = registry.execute_tool(
        "FileWriteTool",
        file_path=str(target),
        content="sample",
        use_firewall=False,
    )
    assert write_result.success

    read_result = registry.execute_tool(
        "FileReadTool",
        file_path=str(target),
        use_firewall=False,
    )
    assert read_result.success
    assert read_result.result == "sample"


def test_calculator_blocks_unsupported_nodes(registry):
    result = registry.execute_tool(
        "CalculatorTool",
        expression="__import__('os').system('ls')",
        use_firewall=False,
    )
    assert not result.success
    assert "decimal" in result.error.lower()


def test_calculator_handles_decimal_precision(registry):
    result = registry.execute_tool(
        "CalculatorTool",
        expression="Decimal('1.25') * 2",
        precision=2,
        use_firewall=False,
    )
    assert result.success
    assert result.result == "2.50"

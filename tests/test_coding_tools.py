import subprocess

import pytest

from src.tools.coding_tools import CodeFormatterTool, CodeLinterTool, CodeExecutorTool


def test_code_formatter_formats_code():
    tool = CodeFormatterTool()
    result = tool.execute("x=1+2")
    assert result.success
    assert "x = 1 + 2" in result.result


def test_code_linter_uses_subprocess(monkeypatch):
    tool = CodeLinterTool()

    class DummyCompleted:
        def __init__(self):
            self.stdout = "ok"
            self.stderr = ""
            self.returncode = 0

    def fake_run(*args, **kwargs):
        assert "pylint" in args[0]
        return DummyCompleted()

    monkeypatch.setattr(subprocess, "run", fake_run)
    output = tool.execute("print('hi')")
    assert output.success
    assert output.result["stdout"] == "ok"


def test_code_executor_runs_python():
    tool = CodeExecutorTool()
    result = tool.execute("print('ping')")
    assert result.success
    assert "ping" in result.result["stdout"]


def test_code_executor_timeout(monkeypatch):
    tool = CodeExecutorTool()

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="python", timeout=kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", fake_run)
    failure = tool.execute("while True: pass", timeout=0.1)
    assert not failure.success
    assert "timed out" in failure.error

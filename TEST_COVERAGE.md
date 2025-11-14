# Test Coverage

This project enforces a minimum **85%** line/branch coverage via the
`[tool.coverage.report] fail_under` setting defined in `pyproject.toml`.
Coverage is measured with `pytest` and `pytest-cov`, tracking both line and
branch metrics for the `src/` tree (GUI/node packages are omitted per
`[tool.coverage.run].omit`).

## How we measure coverage

Use the virtual environment in this repository and run the combined test +
coverage command:

```bash
source venv/bin/activate
python -m pytest --cov=src --cov-report=term --cov-report=xml --cov-branch
```

This command produces:

- Terminal summary with per-module line + branch coverage
- An XML report at `coverage.xml` (for CI or IDEs)
- A `.coverage` data file you can reuse with `coverage html`, etc.

## Latest run (2025-11-14)

- **Command:** `python -m pytest --cov=src --cov-report=term --cov-report=xml --cov-branch`
- **Result:** 78 passed, 2 skipped
- **Total coverage:** **88.28%** (branches enabled)

| Module / Package | Stmts | Miss | Branch | Partial | Coverage |
| ---------------- | ----: | ---: | -----: | ------: | -------: |
| `src/mcp/firewall.py` | 105 | 8 | 44 | 9 | 89% |
| `src/mcp/mcp_client.py` | 108 | 0 | 14 | 1 | 99% |
| `src/mcp/mcp_server.py` | 81 | 7 | 12 | 2 | 90% |
| `src/memory/cache_manager.py` | 98 | 5 | 10 | 2 | 94% |
| `src/tools/accounting_tools.py` | 104 | 19 | 16 | 4 | 79% |
| `src/tools/base.py` | 82 | 8 | 14 | 1 | 91% |
| `src/tools/coding_tools.py` | 91 | 16 | 2 | 1 | 82% |
| `src/tools/web_tools.py` | 113 | 13 | 32 | 6 | 87% |
| `src/tools/writing_tools.py` | 108 | 16 | 30 | 10 | 81% |

> **Note:** Accounting, coding, and writing tool modules are the primary
> remaining areas below the 85% threshold. When adding tests, focus on the
> uncovered line ranges shown in the terminal report for these files.

## Adding new coverage targets

1. Prefer unit tests under `tests/` that exercise the public API of components
   in `src/`. Tests should be deterministic and avoid external network access.
2. If a module is intentionally excluded (e.g., GUI code), update
   `[tool.coverage.run].omit` instead of suppressing warnings in tests.
3. After adding tests, rerun the coverage command above and ensure the total
   stays above 85%. Commit updated reports only when needed for CI tooling.

"""Entry-point for launching the Qt GUI.

This module allows running the GUI with:

    python -m src.gui

It wires up the agent graph construction and shows the main window.
"""

import sys
from typing import Dict, Any

from PySide6.QtWidgets import QApplication

from ..main import build_agent_graph  # assuming this exists in src/main.py
from .main_window import MainWindow


def main(config: Dict[str, Any] | None = None) -> None:
    """Start the Qt application."""
    app = QApplication(sys.argv)

    # Build the agent graph using existing factory
    agent_graph = build_agent_graph()

    window = MainWindow(agent_graph, initial_config=config or {})
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()

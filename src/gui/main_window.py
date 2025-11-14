"""Main Qt GUI window for the agent dashboard.

This module defines the primary application window and wires together
the agent graph with the richer GUI components (chat, monitoring,
settings) and the theme manager.
"""
import sys
from typing import Dict, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSplitter, QListWidget, QTabWidget, QProgressBar,
    QMessageBox, QTreeWidget, QTreeWidgetItem, QToolBar, QAction
)
from PySide6.QtCore import Qt, Signal, QThread, Slot
from loguru import logger

from .widgets.chat_widget import ChatWidget
from .widgets.monitoring_widget import MonitoringWidget
from .components.settings_dialog import SettingsDialog
from .themes.theme_manager import theme_manager, Theme


class ApprovalDialog(QMessageBox):
    """Dialog for approving tool executions."""

    def __init__(self, tool_call: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tool Approval Required")
        self.setIcon(QMessageBox.Question)
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Ok)

        tool_name = tool_call.get("tool", "unknown")
        reason = tool_call.get("reason", "No reason provided")
        params = tool_call.get("params", {})

        self.setText(f"Tool: {tool_name}")
        self.setInformativeText(reason)
        self.setDetailedText(str(params))


class AgentThread(QThread):
    """Thread for running the agent."""

    finished_signal = Signal(dict)
    error_signal = Signal(str)
    status_signal = Signal(str)

    def __init__(self, agent_graph, task: str, session_id: str):
        super().__init__()
        self.agent_graph = agent_graph
        self.task = task
        self.session_id = session_id

    def run(self):
        """Run the agent."""
        try:
            self.status_signal.emit("Running agent...")
            result = self.agent_graph.run(self.task, self.session_id)
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, agent_graph, initial_config: Dict[str, Any] | None = None):
        super().__init__()
        self.agent_graph = agent_graph
        self.current_session = "default"
        self.agent_thread = None
        self.pending_approval = None
        self.config: Dict[str, Any] = initial_config or {}

        self.init_ui()
        logger.info("Main window initialized")

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Abstraction - AI Agent Framework")
        self.setGeometry(100, 100, 1200, 800)

        # Apply initial theme
        initial_theme = self.config.get("gui", {}).get("theme", "light")
        theme_lookup = {"light": Theme.LIGHT, "dark": Theme.DARK, "auto": Theme.AUTO}
        theme_manager.set_theme(theme_lookup.get(initial_theme, Theme.LIGHT))

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Header
        header = QLabel("<h1>Abstraction Agent Framework</h1>")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Toolbar
        toolbar = QToolBar("Main Toolbar", self)
        self.addToolBar(toolbar)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)

        # Status bar-like label
        self.status_bar = QLabel("Ready")
        main_layout.addWidget(self.status_bar)

        # Splitter for main content
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Chat widget
        self.chat_widget = ChatWidget()
        self.chat_widget.message_sent.connect(self.on_user_message)
        splitter.addWidget(self.chat_widget)

        # Right panel - Tabs for details and monitoring
        right_panel = QTabWidget()

        # Tools tab
        self.tools_list = QListWidget()
        right_panel.addTab(self.tools_list, "Tools Used")

        # Reasoning tab
        from PySide6.QtWidgets import QTextEdit
        self.reasoning_display = QTextEdit()
        self.reasoning_display.setReadOnly(True)
        right_panel.addTab(self.reasoning_display, "Reasoning")

        # State tab
        self.state_tree = QTreeWidget()
        self.state_tree.setHeaderLabels(["Property", "Value"])
        right_panel.addTab(self.state_tree, "Agent State")

        # Logs tab
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        right_panel.addTab(self.logs_display, "Logs")

        # Monitoring tab
        self.monitoring_widget = MonitoringWidget()
        right_panel.addTab(self.monitoring_widget, "Monitoring")

        splitter.addWidget(right_panel)
        splitter.setSizes([720, 480])

        main_layout.addWidget(splitter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.log_message("System initialized and ready.")

    def on_user_message(self, task: str):
        """Handle a user message from the chat widget."""
        if not task:
            return

        # Echo message into chat as user bubble
        self.chat_widget.add_message({"role": "user", "content": task})

        # Disable input while processing
        # Disable input while processing
        self.chat_widget.input_field.setEnabled(False)
        self.chat_widget.send_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.set_status("Processing...", "#f39c12")

        # Run agent in thread
        self.agent_thread = AgentThread(self.agent_graph, task, self.current_session)
        self.agent_thread.finished_signal.connect(self.on_agent_finished)
        self.agent_thread.error_signal.connect(self.on_agent_error)
        self.agent_thread.status_signal.connect(self.on_agent_status)
        self.agent_thread.start()

    @Slot(dict)
    def on_agent_finished(self, state: Dict[str, Any]):
        """Handle agent completion."""
        self.progress_bar.setVisible(False)
        self.chat_widget.input_field.setEnabled(True)
        self.chat_widget.send_button.setEnabled(True)
        self.set_status("Ready", theme_manager.get_color("secondary"))

        # Display result in chat widget
        final_answer = state.get('final_answer', 'No answer provided')
        self.chat_widget.add_message({"role": "assistant", "content": final_answer})

        # Update tools list
        for tool in state.get('tools_used', []):
            self.tools_list.addItem(tool)

        # Update reasoning
        reasoning_text = "\n\n".join(state.get('reasoning_steps', []))
        self.reasoning_display.setPlainText(reasoning_text)

        # Update state tree
        self.update_state_tree(state)

        iteration_count = state.get("iteration_count")
        if iteration_count is not None:
            self.log_message(f"Task completed in {iteration_count} iterations")

        # Update monitoring widget with basic stats
        stats = {
            "total_conversations": 1,
            "active_conversations": 0,
            "total_messages": len(state.get("messages", [])),
            "tool_calls": len(state.get("tools_used", [])),
            "average_response_time": state.get("response_time", 0.0),
            "error_rate": 0.0,
        }
        self.monitoring_widget.update_agent_stats(stats)

    @Slot(str)
    def on_agent_error(self, error: str):
        """Handle agent error."""
        self.progress_bar.setVisible(False)
        self.chat_widget.input_field.setEnabled(True)
        self.chat_widget.send_button.setEnabled(True)
        self.set_status("Error", theme_manager.get_color("accent"))

        self.chat_widget.add_message({"role": "system", "content": f"Error: {error}"})
        self.log_message(f"Error: {error}")

        QMessageBox.critical(self, "Agent Error", f"An error occurred:\n{error}")

    @Slot(str)
    def on_agent_status(self, status: str):
        """Handle status updates."""
        self.set_status(status, theme_manager.get_color("primary"))
        self.log_message(status)

    def approval_callback(self, tool_call: Dict[str, Any]) -> bool:
        """
        Callback for tool approvals.

        Args:
            tool_call: Tool call to approve

        Returns:
            True if approved, False otherwise
        """
        dialog = ApprovalDialog(tool_call, self)
        dialog.exec()
        return dialog.approved

    def log_message(self, message: str):
        """Add message to logs."""
        cursor = self.logs_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(f"{message}\n")
        self.logs_display.setTextCursor(cursor)
        self.logs_display.ensureCursorVisible()

    def set_status(self, message: str, color: str):
        """Set status bar message."""
        self.status_bar.setText(message)
        self.status_bar.setStyleSheet(f"color: {color}; padding: 5px;")

    def open_settings(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self.config, self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()

    def on_settings_changed(self, settings: Dict[str, Any]):
        """Handle settings updates from the dialog."""
        # Merge new settings into config
        if settings.get("action") == "clear_cache":
            self.log_message("Cache clear requested (hook up to cache_manager).")
            return

        self.config.update(settings)

        # Apply theme if changed
        gui_conf = settings.get("gui", {})
        if "theme" in gui_conf:
            lookup = {"light": Theme.LIGHT, "dark": Theme.DARK, "auto": Theme.AUTO}
            theme_manager.set_theme(lookup.get(gui_conf["theme"], Theme.LIGHT))

    def update_state_tree(self, state: Dict[str, Any]):
        """Update the state tree view."""
        self.state_tree.clear()

        for key, value in state.items():
            if key == 'messages':
                continue  # Skip messages, shown in chat

            item = QTreeWidgetItem(self.state_tree)
            item.setText(0, key)
            item.setText(1, str(value)[:100])  # Truncate long values

        self.state_tree.expandAll()

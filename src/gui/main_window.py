"""Main Qt GUI window for the agent dashboard.

This module defines the primary application window and wires together
the agent graph with the richer GUI components (chat, monitoring,
settings) and the theme manager.
"""
import sys
import json
from typing import Dict, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QSplitter, QListWidget, QTabWidget, QProgressBar,
    QMessageBox, QTreeWidget, QTreeWidgetItem, QToolBar, QAction, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QThread, Slot
from PySide6.QtGui import QTextCursor
from loguru import logger

from .widgets.chat_widget import ChatWidget
from .widgets.monitoring_widget import MonitoringWidget
from .components.settings_dialog import SettingsDialog
from .themes.theme_manager import theme_manager, Theme
from ..memory.cache_manager import CacheManager


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
        self.cache_manager: CacheManager | None = None
        self.total_conversations: int = 0
        self.active_conversations: int = 0
        self.total_errors: int = 0
        self.total_tasks: int = 0
        gui_conf = self.config.get("gui", {})
        self.tooltips_enabled: bool = gui_conf.get("tooltips", True)
        self.animations_enabled: bool = gui_conf.get("animations", True)
        self.tool_history: list[Dict[str, Any]] = []

        self.init_ui()
        logger.info("Main window initialized")

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Abstraction - AI Agent Framework")
        gui_conf = self.config.get("gui", {})
        width = gui_conf.get("width", 1200)
        height = gui_conf.get("height", 800)
        self.setGeometry(100, 100, width, height)

        # Apply initial theme
        initial_theme = gui_conf.get("theme", "light")
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
        self.tools_list.itemDoubleClicked.connect(self.show_tool_details)
        right_panel.addTab(self.tools_list, "Tools Used")

        # Reasoning tab
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

        # Apply initial GUI-related settings (font size, tooltips, animations)
        self.apply_gui_preferences(gui_conf)

        self.log_message("System initialized and ready.")

    def on_user_message(self, task: str):
        """Handle a user message from the chat widget."""
        if not task:
            return

        # Echo message into chat as user bubble
        self.chat_widget.add_message({"role": "user", "content": task})

        # Disable input while processing
        self.chat_widget.input_field.setEnabled(False)
        self.chat_widget.send_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        if self.animations_enabled:
            self.chat_widget.show_typing_indicator()
        self.set_status("Processing...", "#f39c12")

        # Track active tasks for monitoring
        self.active_conversations += 1
        self.total_tasks += 1

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
        self.chat_widget.hide_typing_indicator()
        if self.active_conversations > 0:
            self.active_conversations -= 1
        self.total_conversations += 1
        self.set_status("Ready", theme_manager.get_color("secondary"))

        # Display result in chat widget
        final_answer = state.get('final_answer', 'No answer provided')
        self.chat_widget.add_message({"role": "assistant", "content": final_answer})

        # Update tools list/history
        tools_used = state.get('tools_used', [])
        self.update_tools_history(tools_used)

        # Update reasoning
        reasoning_text = "\n\n".join(state.get('reasoning_steps', []))
        self.reasoning_display.setPlainText(reasoning_text)

        # Update state tree
        self.update_state_tree(state)

        iteration_count = state.get("iteration_count")
        if iteration_count is not None:
            self.log_message(f"Task completed in {iteration_count} iterations")

        # Update monitoring widget with basic stats
        error_rate = (self.total_errors / self.total_tasks * 100.0) if self.total_tasks else 0.0
        stats = {
            "total_conversations": self.total_conversations,
            "active_conversations": self.active_conversations,
            "total_messages": len(state.get("messages", [])),
            "tool_calls": len(tools_used),
            "average_response_time": state.get("response_time", 0.0),
            "error_rate": error_rate,
            "response_time": state.get("response_time", 0.0),
        }
        self.monitoring_widget.update_agent_stats(stats)

    @Slot(str)
    def on_agent_error(self, error: str):
        """Handle agent error."""
        self.progress_bar.setVisible(False)
        self.chat_widget.input_field.setEnabled(True)
        self.chat_widget.send_button.setEnabled(True)
        self.chat_widget.hide_typing_indicator()
        if self.active_conversations > 0:
            self.active_conversations -= 1
        self.total_errors += 1
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
        result = dialog.exec()
        return result == QMessageBox.Ok

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
            # Lazily initialize cache manager if needed
            if self.cache_manager is None:
                self.cache_manager = CacheManager()
            try:
                self.cache_manager.clear()
                self.log_message("Cache cleared successfully.")
            except Exception as exc:
                self.log_message(f"Failed to clear cache: {exc}")
            return

        self.config.update(settings)

        gui_conf = self.config.get("gui", {})

        # Apply theme and GUI preferences
        theme_value = gui_conf.get("theme")
        if theme_value:
            lookup = {"light": Theme.LIGHT, "dark": Theme.DARK, "auto": Theme.AUTO}
            theme_manager.set_theme(lookup.get(theme_value, Theme.LIGHT))

        self.apply_gui_preferences(gui_conf)

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

    def apply_gui_preferences(self, gui_conf: Dict[str, Any]):
        """Apply GUI-level preferences like font size, window size, and tooltips."""
        font_size = gui_conf.get("font_size")
        if font_size:
            self.setStyleSheet(f"font-size: {font_size}pt;")

        width = gui_conf.get("width")
        height = gui_conf.get("height")
        if width and height:
            self.resize(width, height)

        self.tooltips_enabled = gui_conf.get("tooltips", self.tooltips_enabled)
        self.animations_enabled = gui_conf.get("animations", self.animations_enabled)
        self.set_tooltips_enabled(self.tooltips_enabled)
        if not self.animations_enabled:
            self.chat_widget.hide_typing_indicator()

    def set_tooltips_enabled(self, enabled: bool):
        """Enable or disable tooltips across key widgets."""
        tooltip_text = (lambda text: text if enabled else "")

        self.chat_widget.set_tooltips_enabled(enabled)
        self.status_bar.setToolTip(tooltip_text("Shows the latest agent status."))
        self.tools_list.setToolTip(tooltip_text("History of tools invoked by the agent. Double-click for details."))
        self.reasoning_display.setToolTip(tooltip_text("Agent reasoning traces for the most recent task."))
        self.state_tree.setToolTip(tooltip_text("Snapshot of agent state returned by the workflow."))
        self.logs_display.setToolTip(tooltip_text("Log output for the current GUI session."))
        self.monitoring_widget.setToolTip(tooltip_text("System and agent performance metrics."))
        self.progress_bar.setToolTip(tooltip_text("Indicates that the agent is currently working."))

    def update_tools_history(self, tools_used):
        """Append tool usage information to the history list and UI."""
        if not tools_used:
            return

        for tool in tools_used:
            entry = self._normalize_tool_entry(tool)
            self.tool_history.append(entry)
            display_text = f"{entry['name']} ({entry['status']})"
            self.tools_list.addItem(display_text)

    def _normalize_tool_entry(self, tool: Any) -> Dict[str, Any]:
        """Normalize tool usage data for consistent display."""
        if isinstance(tool, dict):
            name = tool.get("name") or tool.get("tool") or tool.get("id") or "Tool"
            status = tool.get("status") or tool.get("result") or "completed"
            description = tool.get("description") or tool.get("reason") or tool.get("summary", "")
            arguments = tool.get("arguments") or tool.get("params") or tool.get("input") or {}
        else:
            name = str(tool)
            status = "completed"
            description = ""
            arguments = {}

        return {
            "name": name,
            "status": status,
            "description": description,
            "arguments": arguments,
            "raw": tool,
        }

    def show_tool_details(self, item):
        """Display a detailed view for the selected tool invocation."""
        index = self.tools_list.row(item)
        if index < 0 or index >= len(self.tool_history):
            return

        entry = self.tool_history[index]
        details = [
            f"Name: {entry['name']}",
            f"Status: {entry['status']}",
        ]

        if entry.get("description"):
            details.append(f"Description: {entry['description']}")

        arguments = entry.get("arguments")
        if arguments:
            try:
                args_text = json.dumps(arguments, indent=2, ensure_ascii=False)
            except TypeError:
                args_text = str(arguments)
            details.append(f"Arguments:\n{args_text}")

        QMessageBox.information(self, "Tool Details", "\n\n".join(details))

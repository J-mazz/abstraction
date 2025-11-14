"""
Main Qt GUI window for the agent dashboard.
"""
import sys
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QSplitter,
    QListWidget, QTabWidget, QProgressBar, QMessageBox, QDialog,
    QDialogButtonBox, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal, QThread, Slot
from PySide6.QtGui import QFont, QTextCursor
from loguru import logger


class ApprovalDialog(QDialog):
    """Dialog for approving tool executions."""

    def __init__(self, tool_call: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.tool_call = tool_call
        self.approved = False
        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Tool Approval Required")
        self.setModal(True)
        self.resize(500, 300)

        layout = QVBoxLayout()

        # Tool info
        info_label = QLabel(f"<h3>Tool: {self.tool_call['tool']}</h3>")
        layout.addWidget(info_label)

        # Reason
        reason_label = QLabel(f"<b>Reason:</b> {self.tool_call.get('reason', 'No reason provided')}")
        reason_label.setWordWrap(True)
        layout.addWidget(reason_label)

        # Parameters
        params_label = QLabel("<b>Parameters:</b>")
        layout.addWidget(params_label)

        params_text = QTextEdit()
        params_text.setReadOnly(True)
        params_text.setMaximumHeight(100)
        params_text.setPlainText(str(self.tool_call.get('params', {})))
        layout.addWidget(params_text)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.approve)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def approve(self):
        """Approve the tool."""
        self.approved = True
        self.accept()


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

    def __init__(self, agent_graph):
        super().__init__()
        self.agent_graph = agent_graph
        self.current_session = "default"
        self.agent_thread = None
        self.pending_approval = None

        self.init_ui()
        logger.info("Main window initialized")

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Abstraction - AI Agent Framework")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Header
        header = QLabel("<h1>Abstraction Agent Framework</h1>")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Status bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("background-color: #2ecc71; color: white; padding: 5px;")
        main_layout.addWidget(self.status_bar)

        # Splitter for main content
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Chat and input
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Monospace", 10))
        left_layout.addWidget(QLabel("<b>Conversation:</b>"))
        left_layout.addWidget(self.chat_display)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter your task here...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        left_layout.addLayout(input_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        splitter.addWidget(left_panel)

        # Right panel - Tabs for details
        right_panel = QTabWidget()

        # Tools tab
        self.tools_list = QListWidget()
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
        self.logs_display.setFont(QFont("Monospace", 9))
        right_panel.addTab(self.logs_display, "Logs")

        splitter.addWidget(right_panel)

        # Set splitter sizes (60% left, 40% right)
        splitter.setSizes([720, 480])

        main_layout.addWidget(splitter)

        self.log_message("System initialized and ready.")

    def send_message(self):
        """Send a message to the agent."""
        task = self.input_field.text().strip()
        if not task:
            return

        self.input_field.clear()
        self.append_chat(f"You: {task}", "user")

        # Disable input while processing
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
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
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.set_status("Ready", "#2ecc71")

        # Display result
        final_answer = state.get('final_answer', 'No answer provided')
        self.append_chat(f"Agent: {final_answer}", "assistant")

        # Update tools list
        for tool in state.get('tools_used', []):
            self.tools_list.addItem(tool)

        # Update reasoning
        reasoning_text = "\n\n".join(state.get('reasoning_steps', []))
        self.reasoning_display.setPlainText(reasoning_text)

        # Update state tree
        self.update_state_tree(state)

        self.log_message(f"Task completed in {state['iteration_count']} iterations")

    @Slot(str)
    def on_agent_error(self, error: str):
        """Handle agent error."""
        self.progress_bar.setVisible(False)
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.set_status("Error", "#e74c3c")

        self.append_chat(f"Error: {error}", "error")
        self.log_message(f"Error: {error}")

        QMessageBox.critical(self, "Agent Error", f"An error occurred:\n{error}")

    @Slot(str)
    def on_agent_status(self, status: str):
        """Handle status updates."""
        self.set_status(status, "#3498db")
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

    def append_chat(self, message: str, role: str):
        """Append message to chat display."""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        if role == "user":
            cursor.insertHtml(f'<p style="color: #3498db;"><b>{message}</b></p>')
        elif role == "assistant":
            cursor.insertHtml(f'<p style="color: #2ecc71;">{message}</p>')
        elif role == "error":
            cursor.insertHtml(f'<p style="color: #e74c3c;"><b>{message}</b></p>')
        else:
            cursor.insertHtml(f'<p>{message}</p>')

        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

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
        self.status_bar.setStyleSheet(f"background-color: {color}; color: white; padding: 5px;")

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

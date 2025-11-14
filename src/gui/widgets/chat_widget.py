"""
Custom chat widget for conversation display and input.
"""
import re
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QScrollArea, QLabel, QFrame, QSizePolicy, QMenu, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from ..themes.theme_manager import theme_manager


class MessageBubble(QFrame):
    """A message bubble widget for displaying individual messages."""

    def __init__(self, message_data: Dict[str, Any], is_user: bool = False, parent=None):
        super().__init__(parent)
        self.message_data = message_data
        self.is_user = is_user
        self.init_ui()

    def init_ui(self):
        """Initialize the message bubble UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # Header with role and timestamp
        header_layout = QHBoxLayout()

        role_label = QLabel(self.message_data.get('role', 'unknown').title())
        role_label.setStyleSheet(f"""
            font-weight: bold;
            color: {theme_manager.get_color('accent') if self.is_user else theme_manager.get_color('secondary')};
        """)

        timestamp = self.message_data.get('timestamp', '')
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet(f"color: {theme_manager.get_color('muted')}; font-size: 10px;")
            header_layout.addWidget(time_label)

        header_layout.addStretch()
        header_layout.addWidget(role_label)

        layout.addLayout(header_layout)

        # Message content
        content = self.message_data.get('content', '')
        content_label = QLabel()
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setText(self.format_content(content))

        # Set maximum width for readability
        content_label.setMaximumWidth(600)
        content_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        layout.addWidget(content_label)

        # Tool calls if present
        tool_calls = self.message_data.get('tool_calls', [])
        if tool_calls:
            tools_layout = QVBoxLayout()
            tools_label = QLabel("Tool Calls:")
            tools_label.setStyleSheet(f"font-weight: bold; color: {theme_manager.get_color('accent')};")
            tools_layout.addWidget(tools_label)

            for tool_call in tool_calls:
                tool_frame = QFrame()
                tool_frame.setFrameStyle(QFrame.Box)
                tool_frame.setStyleSheet(f"""
                    QFrame {{
                        border: 1px solid {theme_manager.get_color('border')};
                        border-radius: 5px;
                        background-color: {theme_manager.get_color('surface_secondary')};
                    }}
                """)

                tool_layout = QVBoxLayout(tool_frame)

                func_name = tool_call.get('function', {}).get('name', 'Unknown')
                func_label = QLabel(f"Function: {func_name}")
                func_label.setStyleSheet("font-weight: bold;")
                tool_layout.addWidget(func_label)

                args = tool_call.get('function', {}).get('arguments', '{}')
                args_label = QLabel(f"Arguments: {args}")
                args_label.setWordWrap(True)
                args_label.setStyleSheet(f"font-family: monospace; color: {theme_manager.get_color('muted')};")
                tool_layout.addWidget(args_label)

                tools_layout.addWidget(tool_frame)

            layout.addLayout(tools_layout)

        self.setLayout(layout)

        # Style the bubble
        self.setStyleSheet(f"""
            MessageBubble {{
                background-color: {theme_manager.get_color('surface') if not self.is_user else theme_manager.get_color('accent_light')};
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 10px;
                margin: 2px;
            }}
        """)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    def format_content(self, content: str) -> str:
        """Format message content with basic markdown-like formatting."""
        if not content:
            return ""

        # Escape HTML
        content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Basic formatting
        content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)  # Bold
        content = re.sub(r'\*(.*?)\*', r'<i>\1</i>', content)      # Italic
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)  # Inline code

        # Code blocks
        content = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', content, flags=re.DOTALL)

        # Links
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', content)

        # Line breaks
        content = content.replace('\n', '<br>')

        return f'<span style="color: {theme_manager.get_color("text")};">{content}</span>'

    def update_theme(self):
        """Update the bubble when theme changes."""
        # Re-apply styles
        self.setStyleSheet(f"""
            MessageBubble {{
                background-color: {theme_manager.get_color('surface') if not self.is_user else theme_manager.get_color('accent_light')};
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 10px;
                margin: 2px;
            }}
        """)


class TypingIndicator(QWidget):
    """Typing indicator widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dots = []
        self.init_ui()
        self.start_animation()

    def init_ui(self):
        """Initialize the typing indicator UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        layout.addWidget(QLabel("Agent is thinking"))
        layout.addStretch()

        for i in range(3):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {theme_manager.get_color('muted')};")
            layout.addWidget(dot)
            self.dots.append(dot)

        self.setLayout(layout)

    def start_animation(self):
        """Start the typing animation."""
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate_dots)
        self.animation_timer.start(500)  # Update every 500ms
        self.animation_step = 0

    def animate_dots(self):
        """Animate the dots."""
        self.animation_step = (self.animation_step + 1) % 4
        for i, dot in enumerate(self.dots):
            if i < self.animation_step:
                dot.setStyleSheet(f"color: {theme_manager.get_color('accent')};")
            else:
                dot.setStyleSheet(f"color: {theme_manager.get_color('muted')};")

    def stop_animation(self):
        """Stop the typing animation."""
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()


class ChatWidget(QWidget):
    """Main chat widget for displaying conversations and input."""

    message_sent = Signal(str)
    tool_executed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []
        self.typing_indicator = None
        self.tooltips_enabled = True
        self.init_ui()

    def init_ui(self):
        """Initialize the chat widget UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Chat display area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Container for messages
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(5)

        self.scroll_area.setWidget(self.messages_container)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {theme_manager.get_color('background')};
            }}
        """)

        layout.addWidget(self.scroll_area)

        # Input area
        input_layout = QHBoxLayout()

        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 5px;
                background-color: {theme_manager.get_color('surface')};
                color: {theme_manager.get_color('text')};
                padding: 5px;
            }}
        """)

        # Connect enter key to send
        self.input_field.installEventFilter(self)

        input_layout.addWidget(self.input_field)

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme_manager.get_color('accent')};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme_manager.get_color('accent_dark')};
            }}
            QPushButton:pressed {{
                background-color: {theme_manager.get_color('accent_darker')};
            }}
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        self.setLayout(layout)

        # Context menu for messages
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def eventFilter(self, obj, event):
        """Handle key events for the input field."""
        if obj == self.input_field and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def add_message(self, message_data: Dict[str, Any]):
        """Add a message to the chat."""
        self.messages.append(message_data)

        # Determine if it's a user message
        is_user = message_data.get('role') == 'user'

        # Create message bubble
        message_bubble = MessageBubble(message_data, is_user)
        self.messages_layout.addWidget(message_bubble)

        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)

    def show_typing_indicator(self):
        """Show the typing indicator."""
        if self.typing_indicator is None:
            self.typing_indicator = TypingIndicator()
            self.messages_layout.addWidget(self.typing_indicator)
            QTimer.singleShot(100, self.scroll_to_bottom)

    def hide_typing_indicator(self):
        """Hide the typing indicator."""
        if self.typing_indicator:
            self.typing_indicator.stop_animation()
            self.messages_layout.removeWidget(self.typing_indicator)
            self.typing_indicator.deleteLater()
            self.typing_indicator = None

    def clear_chat(self):
        """Clear all messages from the chat."""
        # Remove all message bubbles
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.messages.clear()
        self.hide_typing_indicator()

    def scroll_to_bottom(self):
        """Scroll to the bottom of the chat."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        """Send the current message."""
        message = self.input_field.toPlainText().strip()
        if message:
            # Clear input
            self.input_field.clear()

            # Emit signal
            self.message_sent.emit(message)

    def show_context_menu(self, position):
        """Show context menu for messages."""
        menu = QMenu(self)

        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(self.copy_selected_text)

        clear_action = menu.addAction("Clear Chat")
        clear_action.triggered.connect(self.clear_chat)

        menu.exec(self.mapToGlobal(position))

    def copy_selected_text(self):
        """Copy selected text to clipboard."""
        # Get selected text from input field or messages
        selected_text = ""

        # Check input field first
        cursor = self.input_field.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
        else:
            # Fallback to copying the last message content
            if self.messages:
                last_message = self.messages[-1]
                selected_text = last_message.get('content', '')

        if selected_text:
            QApplication.clipboard().setText(selected_text)

    def set_tooltips_enabled(self, enabled: bool):
        """Enable or disable tooltips for chat controls."""
        self.tooltips_enabled = enabled

        input_tip = "Compose a new instruction or question." if enabled else ""
        send_tip = "Send the current message to the agent." if enabled else ""

        self.input_field.setToolTip(input_tip)
        self.send_button.setToolTip(send_tip)

    def update_theme(self):
        """Update the widget when theme changes."""
        # Update styles
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {theme_manager.get_color('background')};
            }}
        """)

        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 5px;
                background-color: {theme_manager.get_color('surface')};
                color: {theme_manager.get_color('text')};
                padding: 5px;
            }}
        """)

        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme_manager.get_color('accent')};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme_manager.get_color('accent_dark')};
            }}
            QPushButton:pressed {{
                background-color: {theme_manager.get_color('accent_darker')};
            }}
        """)

        # Update all message bubbles
        for i in range(self.messages_layout.count()):
            widget = self.messages_layout.itemAt(i).widget()
            if isinstance(widget, MessageBubble):
                widget.update_theme()

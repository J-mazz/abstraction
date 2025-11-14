"""
Theme management system for the GUI.
"""
from enum import Enum
from typing import Dict, Any
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


class Theme(Enum):
    """Available themes."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ThemeManager:
    """Manages application themes and styling."""

    # Light theme colors
    LIGHT_COLORS = {
        'primary': '#3498db',
        'secondary': '#2ecc71',
        'accent': '#e74c3c',
        'warning': '#f39c12',
        'background': '#f8f9fa',
        'surface': '#ffffff',
        'text': '#2c3e50',
        'text_secondary': '#7f8c8d',
        'border': '#dee2e6',
        'hover': '#e9ecef',
        'selected': '#007bff',
    }

    # Dark theme colors
    DARK_COLORS = {
        'primary': '#5dade2',
        'secondary': '#58d68d',
        'accent': '#ec7063',
        'warning': '#f7dc6f',
        'background': '#1a1a1a',
        'surface': '#2d2d2d',
        'text': '#e8eaed',
        'text_secondary': '#9aa0a6',
        'border': '#5f6368',
        'hover': '#3c4043',
        'selected': '#8ab4f8',
    }

    def __init__(self):
        self.current_theme = Theme.LIGHT
        self.colors = self.LIGHT_COLORS.copy()

    def set_theme(self, theme: Theme):
        """Set the application theme."""
        self.current_theme = theme

        if theme == Theme.DARK:
            self.colors = self.DARK_COLORS.copy()
        elif theme == Theme.LIGHT:
            self.colors = self.LIGHT_COLORS.copy()
        elif theme == Theme.AUTO:
            # Auto-detect based on system preference
            app = QApplication.instance()
            if app and app.palette().color(QPalette.Window).lightness() < 128:
                self.colors = self.DARK_COLORS.copy()
                self.current_theme = Theme.DARK
            else:
                self.colors = self.LIGHT_COLORS.copy()
                self.current_theme = Theme.LIGHT

        self._apply_theme()

    def get_color(self, name: str) -> str:
        """Get a color by name."""
        return self.colors.get(name, '#000000')

    def get_stylesheet(self) -> str:
        """Generate Qt stylesheet for current theme."""
        return f"""
        /* Main application styling */
        QMainWindow {{
            background-color: {self.get_color('background')};
            color: {self.get_color('text')};
        }}

        QWidget {{
            background-color: {self.get_color('surface')};
            color: {self.get_color('text')};
            border: 1px solid {self.get_color('border')};
        }}

        /* Buttons */
        QPushButton {{
            background-color: {self.get_color('primary')};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {self.get_color('primary')}dd;
        }}

        QPushButton:pressed {{
            background-color: {self.get_color('primary')}bb;
        }}

        QPushButton:disabled {{
            background-color: {self.get_color('border')};
            color: {self.get_color('text_secondary')};
        }}

        /* Input fields */
        QLineEdit, QTextEdit {{
            border: 2px solid {self.get_color('border')};
            border-radius: 4px;
            padding: 8px;
            background-color: {self.get_color('surface')};
            color: {self.get_color('text')};
        }}

        QLineEdit:focus, QTextEdit:focus {{
            border-color: {self.get_color('primary')};
        }}

        /* Tabs */
        QTabWidget::pane {{
            border: 1px solid {self.get_color('border')};
            background-color: {self.get_color('surface')};
        }}

        QTabBar::tab {{
            background-color: {self.get_color('hover')};
            color: {self.get_color('text')};
            padding: 8px 16px;
            border: 1px solid {self.get_color('border')};
            margin-right: 2px;
        }}

        QTabBar::tab:selected {{
            background-color: {self.get_color('surface')};
            border-bottom: 2px solid {self.get_color('primary')};
        }}

        /* Lists and trees */
        QListWidget, QTreeWidget {{
            background-color: {self.get_color('surface')};
            alternate-background-color: {self.get_color('hover')};
            border: 1px solid {self.get_color('border')};
        }}

        QListWidget::item:selected, QTreeWidget::item:selected {{
            background-color: {self.get_color('selected')}33;
        }}

        /* Progress bars */
        QProgressBar {{
            border: 1px solid {self.get_color('border')};
            border-radius: 4px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {self.get_color('primary')};
            border-radius: 2px;
        }}

        /* Status bar */
        QStatusBar {{
            background-color: {self.get_color('surface')};
            border-top: 1px solid {self.get_color('border')};
        }}

        /* Scroll bars */
        QScrollBar:vertical {{
            background-color: {self.get_color('hover')};
            width: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {self.get_color('border')};
            border-radius: 6px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {self.get_color('text_secondary')};
        }}

        /* Dialogs */
        QDialog {{
            background-color: {self.get_color('surface')};
            color: {self.get_color('text')};
        }}

        QMessageBox {{
            background-color: {self.get_color('surface')};
        }}

        QMessageBox QLabel {{
            color: {self.get_color('text')};
        }}
        """

    def _apply_theme(self):
        """Apply the current theme to the application."""
        app = QApplication.instance()
        if app:
            stylesheet = self.get_stylesheet()
            app.setStyleSheet(stylesheet)

            # Update palette for better system integration
            palette = app.palette()

            if self.current_theme == Theme.DARK:
                palette.setColor(QPalette.Window, QColor(self.get_color('background')))
                palette.setColor(QPalette.WindowText, QColor(self.get_color('text')))
                palette.setColor(QPalette.Base, QColor(self.get_color('surface')))
                palette.setColor(QPalette.AlternateBase, QColor(self.get_color('hover')))
                palette.setColor(QPalette.Text, QColor(self.get_color('text')))
                palette.setColor(QPalette.Button, QColor(self.get_color('surface')))
                palette.setColor(QPalette.ButtonText, QColor(self.get_color('text')))
            else:
                # Reset to system default for light theme
                app.setPalette(app.style().standardPalette())

            app.setPalette(palette)


# Global theme manager instance
theme_manager = ThemeManager()

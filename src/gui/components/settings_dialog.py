"""
Settings and preferences dialog.
"""
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QCheckBox, QGroupBox, QTabWidget, QWidget,
    QDialogButtonBox, QMessageBox, QFormLayout, QLineEdit,
    QSlider, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from ..themes.theme_manager import Theme, theme_manager


class SettingsDialog(QDialog):
    """Settings and preferences dialog."""

    settings_changed = Signal(dict)

    def __init__(self, current_config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.current_config = current_config.copy()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Settings & Preferences")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout()

        # Tab widget for different settings categories
        self.tab_widget = QTabWidget()

        # General settings tab
        self.general_tab = self.create_general_tab()
        self.tab_widget.addTab(self.general_tab, "General")

        # Agent settings tab
        self.agent_tab = self.create_agent_tab()
        self.tab_widget.addTab(self.agent_tab, "Agent")

        # GUI settings tab
        self.gui_tab = self.create_gui_tab()
        self.tab_widget.addTab(self.gui_tab, "Interface")

        # Memory settings tab
        self.memory_tab = self.create_memory_tab()
        self.tab_widget.addTab(self.memory_tab, "Memory")

        layout.addWidget(self.tab_widget)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def create_general_tab(self) -> QWidget:
        """Create the general settings tab."""
        widget = QWidget()
        layout = QFormLayout()

        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        layout.addRow("Theme:", self.theme_combo)

        # Logging level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        layout.addRow("Log Level:", self.log_level_combo)

        # Auto-save conversations
        self.auto_save_check = QCheckBox("Auto-save conversations")
        layout.addRow("", self.auto_save_check)

        # Confirm before tool execution
        self.confirm_tools_check = QCheckBox("Confirm before tool execution")
        self.confirm_tools_check.setChecked(True)
        layout.addRow("", self.confirm_tools_check)

        widget.setLayout(layout)
        return widget

    def create_agent_tab(self) -> QWidget:
        """Create the agent settings tab."""
        widget = QWidget()
        layout = QFormLayout()

        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "mistral-7b-instruct-v0.3",
            "mistral-7b-instruct-v0.1",
            "mixtral-8x7b-instruct-v0.1"
        ])
        layout.addRow("Model:", self.model_combo)

        # Temperature slider
        temp_layout = QHBoxLayout()
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 20)  # 0.0 to 2.0
        self.temp_slider.setValue(7)  # 0.7 default
        self.temp_label = QLabel("0.7")
        self.temp_slider.valueChanged.connect(
            lambda v: self.temp_label.setText(f"{v/10:.1f}")
        )
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_label)
        layout.addRow("Temperature:", temp_layout)

        # Max tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 10000)
        self.max_tokens_spin.setValue(4096)
        layout.addRow("Max Tokens:", self.max_tokens_spin)

        # Max iterations
        self.max_iterations_spin = QSpinBox()
        self.max_iterations_spin.setRange(1, 10)
        self.max_iterations_spin.setValue(3)
        layout.addRow("Max Iterations:", self.max_iterations_spin)

        # Confidence threshold
        confidence_layout = QHBoxLayout()
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(50, 95)  # 0.5 to 0.95
        self.confidence_slider.setValue(70)  # 0.7 default
        self.confidence_label = QLabel("0.7")
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"{v/100:.2f}")
        )
        confidence_layout.addWidget(self.confidence_slider)
        confidence_layout.addWidget(self.confidence_label)
        layout.addRow("Confidence Threshold:", confidence_layout)

        widget.setLayout(layout)
        return widget

    def create_gui_tab(self) -> QWidget:
        """Create the GUI settings tab."""
        widget = QWidget()
        layout = QFormLayout()

        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        layout.addRow("Font Size:", self.font_size_spin)

        # Window size
        size_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(800, 2000)
        self.width_spin.setValue(1200)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(600, 1500)
        self.height_spin.setValue(800)
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(self.height_spin)
        layout.addRow("Window Size:", size_layout)

        # Show tooltips
        self.tooltips_check = QCheckBox("Show tooltips")
        self.tooltips_check.setChecked(True)
        layout.addRow("", self.tooltips_check)

        # Enable animations
        self.animations_check = QCheckBox("Enable animations")
        self.animations_check.setChecked(True)
        layout.addRow("", self.animations_check)

        widget.setLayout(layout)
        return widget

    def create_memory_tab(self) -> QWidget:
        """Create the memory settings tab."""
        widget = QWidget()
        layout = QFormLayout()

        # Cache size
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(100, 10000)
        self.cache_size_spin.setValue(1000)
        self.cache_size_spin.setSuffix(" MB")
        layout.addRow("Cache Size:", self.cache_size_spin)

        # TTL
        self.ttl_spin = QSpinBox()
        self.ttl_spin.setRange(1, 168)  # 1 hour to 1 week
        self.ttl_spin.setValue(24)
        self.ttl_spin.setSuffix(" hours")
        layout.addRow("Cache TTL:", self.ttl_spin)

        # Memory type
        self.memory_type_combo = QComboBox()
        self.memory_type_combo.addItems(["disk", "redis", "sqlite"])
        layout.addRow("Memory Type:", self.memory_type_combo)

        # Clear cache button
        from PySide6.QtWidgets import QPushButton
        self.clear_cache_btn = QPushButton("Clear Cache")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        layout.addRow("", self.clear_cache_btn)

        widget.setLayout(layout)
        return widget

    def load_settings(self):
        """Load current settings into the UI."""
        # General settings
        theme_map = {"light": 0, "dark": 1, "auto": 2}
        theme_value = self.current_config.get('gui', {}).get('theme', 'light')
        self.theme_combo.setCurrentIndex(theme_map.get(theme_value, 0))

        log_level_map = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
        log_level = self.current_config.get('logging', {}).get('level', 'INFO')
        self.log_level_combo.setCurrentIndex(log_level_map.get(log_level, 1))

        self.auto_save_check.setChecked(
            self.current_config.get('gui', {}).get('auto_save', True)
        )
        self.confirm_tools_check.setChecked(
            self.current_config.get('human_in_loop', {}).get('enabled', True)
        )

        # Agent settings
        agent_config = self.current_config.get('agent', {})
        model_name = agent_config.get('model_name', 'mistral-7b-instruct-v0.3')
        model_index = self.model_combo.findText(model_name)
        if model_index >= 0:
            self.model_combo.setCurrentIndex(model_index)

        temp_value = int((agent_config.get('temperature', 0.7) * 10))
        self.temp_slider.setValue(temp_value)

        self.max_tokens_spin.setValue(agent_config.get('max_tokens', 4096))
        self.max_iterations_spin.setValue(
            self.current_config.get('reasoning', {}).get('max_iterations', 3)
        )

        confidence_value = int((
            self.current_config.get('reasoning', {}).get('min_confidence_threshold', 0.7) * 100
        ))
        self.confidence_slider.setValue(confidence_value)

        # GUI settings
        gui_config = self.current_config.get('gui', {})
        self.font_size_spin.setValue(gui_config.get('font_size', 10))
        self.width_spin.setValue(gui_config.get('width', 1200))
        self.height_spin.setValue(gui_config.get('height', 800))
        self.tooltips_check.setChecked(gui_config.get('tooltips', True))
        self.animations_check.setChecked(gui_config.get('animations', True))

        # Memory settings
        memory_config = self.current_config.get('memory', {})
        self.cache_size_spin.setValue(memory_config.get('max_cache_size_mb', 1000))
        self.ttl_spin.setValue(memory_config.get('ttl_hours', 24))
        self.memory_type_combo.setCurrentText(memory_config.get('type', 'disk'))

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings from the UI."""
        theme_map = {0: "light", 1: "dark", 2: "auto"}
        log_level_map = {0: "DEBUG", 1: "INFO", 2: "WARNING", 3: "ERROR"}

        return {
            'gui': {
                'theme': theme_map[self.theme_combo.currentIndex()],
                'font_size': self.font_size_spin.value(),
                'width': self.width_spin.value(),
                'height': self.height_spin.value(),
                'tooltips': self.tooltips_check.isChecked(),
                'animations': self.animations_check.isChecked(),
                'auto_save': self.auto_save_check.isChecked(),
            },
            'logging': {
                'level': log_level_map[self.log_level_combo.currentIndex()],
            },
            'agent': {
                'model_name': self.model_combo.currentText(),
                'temperature': self.temp_slider.value() / 10.0,
                'max_tokens': self.max_tokens_spin.value(),
            },
            'reasoning': {
                'max_iterations': self.max_iterations_spin.value(),
                'min_confidence_threshold': self.confidence_slider.value() / 100.0,
            },
            'human_in_loop': {
                'enabled': self.confirm_tools_check.isChecked(),
            },
            'memory': {
                'type': self.memory_type_combo.currentText(),
                'max_cache_size_mb': self.cache_size_spin.value(),
                'ttl_hours': self.ttl_spin.value(),
            }
        }

    def apply_settings(self):
        """Apply the current settings."""
        new_settings = self.get_settings()
        self.settings_changed.emit(new_settings)
        self.current_config.update(new_settings)

        # Apply theme immediately
        theme_map = {"light": Theme.LIGHT, "dark": Theme.DARK, "auto": Theme.AUTO}
        theme = theme_map.get(new_settings['gui']['theme'], Theme.LIGHT)
        theme_manager.set_theme(theme)

        QMessageBox.information(self, "Settings Applied",
                               "Settings have been applied successfully!")

    def clear_cache(self):
        """Clear the application cache."""
        reply = QMessageBox.question(
            self, "Clear Cache",
            "Are you sure you want to clear all cached data? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Emit signal to clear cache
            self.settings_changed.emit({'action': 'clear_cache'})
            QMessageBox.information(self, "Cache Cleared",
                                   "Cache has been cleared successfully!")

    def accept(self):
        """Accept the dialog and apply settings."""
        self.apply_settings()
        super().accept()

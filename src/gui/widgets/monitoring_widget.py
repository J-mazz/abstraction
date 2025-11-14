"""
Monitoring dashboard widget for real-time performance metrics.
"""
from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QProgressBar, QGridLayout, QGroupBox, QSplitter,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtCharts import QChartView, QChart, QLineSeries, QValueAxis
from PySide6.QtGui import QPainter, QColor, QBrush
from ..themes.theme_manager import theme_manager
import psutil
import time
from datetime import datetime


class MetricCard(QFrame):
    """A card widget for displaying a single metric."""

    def __init__(self, title: str, value: str = "0", unit: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.unit = unit
        self.init_ui()

    def init_ui(self):
        """Initialize the metric card UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            font-weight: bold;
            color: {theme_manager.get_color('text')};
            font-size: 12px;
        """)
        layout.addWidget(title_label)

        # Value
        self.value_label = QLabel(f"{self.value} {self.unit}")
        self.value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {theme_manager.get_color('accent')};
        """)
        layout.addWidget(self.value_label)

        self.setLayout(layout)

        # Style the card
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: {theme_manager.get_color('surface')};
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 8px;
            }}
        """)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setMinimumHeight(80)

    def update_value(self, value: str):
        """Update the displayed value."""
        self.value = value
        self.value_label.setText(f"{self.value} {self.unit}")


class PerformanceChart(QChartView):
    """Chart widget for displaying performance metrics over time."""

    def __init__(self, title: str, max_points: int = 50, parent=None):
        super().__init__(parent)
        self.title = title
        self.max_points = max_points
        self.series = QLineSeries()
        self.series.setName(title)

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle(title)
        text_brush = QBrush(QColor(theme_manager.get_color('text')))
        self.chart.setTitleBrush(text_brush)

        # Create axes
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Time (seconds)")
        self.axis_x.setTitleBrush(text_brush)
        self.axis_x.setLabelsBrush(text_brush)

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Value")
        self.axis_y.setTitleBrush(text_brush)
        self.axis_y.setLabelsBrush(text_brush)

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)

        # Style the chart
        self.chart.setBackgroundBrush(QColor(theme_manager.get_color('background')))
        self.chart.setPlotAreaBackgroundBrush(QColor(theme_manager.get_color('surface')))
        self.chart.setPlotAreaBackgroundVisible(True)

        self.setChart(self.chart)
        self.setRenderHint(QPainter.Antialiasing)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.data_points = []
        self.start_time = time.time()

    def add_point(self, value: float):
        """Add a new data point to the chart."""
        current_time = time.time() - self.start_time

        # Add point to series
        self.series.append(current_time, value)
        self.data_points.append((current_time, value))

        # Remove old points if we exceed max_points
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
            self.series.remove(0)

        # Update axes ranges
        if self.data_points:
            times = [p[0] for p in self.data_points]
            values = [p[1] for p in self.data_points]

            self.axis_x.setRange(min(times), max(times))
            self.axis_y.setRange(min(values) * 0.9, max(values) * 1.1)

    def update_theme(self):
        """Update chart colors when theme changes."""
        text_brush = QBrush(QColor(theme_manager.get_color('text')))
        self.chart.setTitleBrush(text_brush)
        self.chart.setBackgroundBrush(QColor(theme_manager.get_color('background')))
        self.chart.setPlotAreaBackgroundBrush(QColor(theme_manager.get_color('surface')))

        self.axis_x.setTitleBrush(text_brush)
        self.axis_x.setLabelsBrush(text_brush)
        self.axis_y.setTitleBrush(text_brush)
        self.axis_y.setLabelsBrush(text_brush)


class SystemMonitor(QWidget):
    """Widget for monitoring system resources."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.start_monitoring()

    def init_ui(self):
        """Initialize the system monitor UI."""
        layout = QVBoxLayout()

        # CPU Usage
        cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QVBoxLayout()

        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_label = QLabel("CPU: 0%")
        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addWidget(self.cpu_progress)

        cpu_group.setLayout(cpu_layout)
        layout.addWidget(cpu_group)

        # Memory Usage
        memory_group = QGroupBox("Memory Usage")
        memory_layout = QVBoxLayout()

        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_label = QLabel("Memory: 0%")
        memory_layout.addWidget(self.memory_label)
        memory_layout.addWidget(self.memory_progress)

        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)

        # Disk Usage
        disk_group = QGroupBox("Disk Usage")
        disk_layout = QVBoxLayout()

        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        self.disk_label = QLabel("Disk: 0%")
        disk_layout.addWidget(self.disk_label)
        disk_layout.addWidget(self.disk_progress)

        disk_group.setLayout(disk_layout)
        layout.addWidget(disk_group)

        self.setLayout(layout)

    def start_monitoring(self):
        """Start system monitoring."""
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.update_system_stats)
        self.monitor_timer.start(2000)  # Update every 2 seconds

        # Initial update
        self.update_system_stats()

    def update_system_stats(self):
        """Update system statistics."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_progress.setValue(int(cpu_percent))
            self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")

            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_progress.setValue(int(memory_percent))
            self.memory_label.setText(f"Memory: {memory_percent:.1f}% ({memory.used/1024/1024/1024:.1f}GB / {memory.total/1024/1024/1024:.1f}GB)")

            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            self.disk_progress.setValue(int(disk_percent))
            self.disk_label.setText(f"Disk: {disk_percent:.1f}% ({disk.used/1024/1024/1024:.1f}GB / {disk.total/1024/1024/1024:.1f}GB)")

        except Exception as e:
            print(f"Error updating system stats: {e}")


class AgentMonitor(QWidget):
    """Widget for monitoring agent performance and activity."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent_stats = {
            'total_conversations': 0,
            'active_conversations': 0,
            'total_messages': 0,
            'tool_calls': 0,
            'average_response_time': 0.0,
            'error_rate': 0.0
        }
        self.init_ui()

    def init_ui(self):
        """Initialize the agent monitor UI."""
        layout = QVBoxLayout()

        # Metrics grid
        metrics_layout = QGridLayout()

        # Row 1
        self.conversations_card = MetricCard("Total Conversations", "0")
        self.active_card = MetricCard("Active", "0")
        metrics_layout.addWidget(self.conversations_card, 0, 0)
        metrics_layout.addWidget(self.active_card, 0, 1)

        # Row 2
        self.messages_card = MetricCard("Messages", "0")
        self.tools_card = MetricCard("Tool Calls", "0")
        metrics_layout.addWidget(self.messages_card, 1, 0)
        metrics_layout.addWidget(self.tools_card, 1, 1)

        # Row 3
        self.response_time_card = MetricCard("Avg Response", "0", "s")
        self.error_rate_card = MetricCard("Error Rate", "0", "%")
        metrics_layout.addWidget(self.response_time_card, 2, 0)
        metrics_layout.addWidget(self.error_rate_card, 2, 1)

        layout.addLayout(metrics_layout)

        # Performance chart
        self.response_time_chart = PerformanceChart("Response Time (seconds)")
        layout.addWidget(self.response_time_chart)

        self.setLayout(layout)

    def update_stats(self, stats: Dict[str, Any]):
        """Update agent statistics."""
        self.agent_stats.update(stats)

        # Update cards
        self.conversations_card.update_value(str(self.agent_stats['total_conversations']))
        self.active_card.update_value(str(self.agent_stats['active_conversations']))
        self.messages_card.update_value(str(self.agent_stats['total_messages']))
        self.tools_card.update_value(str(self.agent_stats['tool_calls']))
        self.response_time_card.update_value(f"{self.agent_stats['average_response_time']:.2f}")
        self.error_rate_card.update_value(f"{self.agent_stats['error_rate']:.1f}")

        # Update chart
        if 'response_time' in stats:
            self.response_time_chart.add_point(stats['response_time'])


class MonitoringWidget(QWidget):
    """Main monitoring dashboard widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the monitoring widget UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("System & Agent Monitoring")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {theme_manager.get_color('text')};
            margin-bottom: 10px;
        """)
        layout.addWidget(title)

        # Splitter for system and agent monitoring
        splitter = QSplitter(Qt.Horizontal)

        # System monitor
        self.system_monitor = SystemMonitor()
        splitter.addWidget(self.system_monitor)

        # Agent monitor
        self.agent_monitor = AgentMonitor()
        splitter.addWidget(self.agent_monitor)

        # Set splitter proportions
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)
        self.setLayout(layout)

    def update_agent_stats(self, stats: Dict[str, Any]):
        """Update agent statistics."""
        self.agent_monitor.update_stats(stats)

    def update_theme(self):
        """Update widget when theme changes."""
        # Update system monitor progress bars
        self.system_monitor.cpu_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {theme_manager.get_color('accent')};
            }}
        """)

        self.system_monitor.memory_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {theme_manager.get_color('secondary')};
            }}
        """)

        self.system_monitor.disk_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {theme_manager.get_color('warning')};
            }}
        """)

        # Update agent monitor
        self.agent_monitor.response_time_chart.update_theme()

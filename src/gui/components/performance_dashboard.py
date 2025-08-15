from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from src.utils.performance_analytics import PerformanceAnalytics


class PerformanceDashboard(QWidget):
    """Interactive dashboard for OCR performance monitoring"""

    def __init__(self, analytics: PerformanceAnalytics):
        super().__init__()
        self.analytics = analytics
        self.setup_ui()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def setup_ui(self):
        """Set up the dashboard UI"""
        layout = QVBoxLayout(self)

        # Create tab widget
        tabs = QTabWidget()

        # Add tabs
        tabs.addTab(self._create_overview_tab(), "Overview")
        tabs.addTab(self._create_templates_tab(), "Templates")
        tabs.addTab(self._create_errors_tab(), "Error Analysis")
        tabs.addTab(self._create_trends_tab(), "Trends")

        layout.addWidget(tabs)

    def _create_overview_tab(self) -> QWidget:
        """Create overview dashboard tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Add time range selector
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Time Range:"))
        self.time_range = QComboBox()
        self.time_range.addItems(["Last 24 Hours", "Last Week", "Last Month"])
        self.time_range.currentTextChanged.connect(self.refresh_data)
        range_layout.addWidget(self.time_range)
        range_layout.addStretch()
        layout.addLayout(range_layout)

        # Create metrics grid
        metrics_layout = QHBoxLayout()

        # Add key metrics
        summary = self.analytics.get_performance_summary(7)  # Default to week view
        metrics = [
            ("Documents Processed", str(summary.get("total_documents", 0))),
            (
                "Avg. Processing Time",
                f"{summary.get('average_processing_time', 0):.2f}s",
            ),
            ("Avg. Confidence", f"{summary.get('average_confidence', 0):.1f}%"),
            ("Cache Hit Rate", f"{summary.get('cache_hit_rate', 0):.1f}%"),
        ]

        for label, value in metrics:
            metric_widget = self._create_metric_widget(label, value)
            metrics_layout.addWidget(metric_widget)

        layout.addLayout(metrics_layout)

        # Add performance chart
        self.performance_figure = Figure(figsize=(8, 4))
        self.performance_canvas = FigureCanvasQTAgg(self.performance_figure)
        layout.addWidget(self.performance_canvas)

        return tab

    def _create_templates_tab(self) -> QWidget:
        """Create templates performance tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Add template statistics table
        self.template_table = QTableWidget()
        self.template_table.setColumnCount(5)
        self.template_table.setHorizontalHeaderLabels(
            [
                "Template Type",
                "Count",
                "Avg. Time (s)",
                "Avg. Confidence (%)",
                "Cache Hit Rate (%)",
            ]
        )
        layout.addWidget(self.template_table)

        # Add template comparison chart
        self.template_figure = Figure(figsize=(8, 4))
        self.template_canvas = FigureCanvasQTAgg(self.template_figure)
        layout.addWidget(self.template_canvas)

        return tab

    def _create_errors_tab(self) -> QWidget:
        """Create error analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Add error statistics table
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(4)
        self.error_table.setHorizontalHeaderLabels(
            ["Template Type", "Total Errors", "Total Documents", "Error Rate (%)"]
        )
        layout.addWidget(self.error_table)

        # Add error distribution chart
        self.error_figure = Figure(figsize=(8, 4))
        self.error_canvas = FigureCanvasQTAgg(self.error_figure)
        layout.addWidget(self.error_canvas)

        return tab

    def _create_trends_tab(self) -> QWidget:
        """Create trends analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Add metric selector
        metric_layout = QHBoxLayout()
        metric_layout.addWidget(QLabel("Metric:"))
        self.metric_selector = QComboBox()
        self.metric_selector.addItems(
            ["Processing Time", "Confidence Score", "Cache Hit Rate", "Error Rate"]
        )
        self.metric_selector.currentTextChanged.connect(self.update_trend_chart)
        metric_layout.addWidget(self.metric_selector)
        metric_layout.addStretch()
        layout.addLayout(metric_layout)

        # Add trend chart
        self.trend_figure = Figure(figsize=(8, 4))
        self.trend_canvas = FigureCanvasQTAgg(self.trend_figure)
        layout.addWidget(self.trend_canvas)

        return tab

    def _create_metric_widget(self, label: str, value: str) -> QWidget:
        """Create a widget for displaying a metric"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        desc_label = QLabel(label)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(value_label)
        layout.addWidget(desc_label)

        widget.setStyleSheet(
            """
            QWidget {
                background-color: #f0f0f0;
                border-radius: 5px;
                padding: 10px;
            }
        """
        )

        return widget

    def refresh_data(self):
        """Refresh all dashboard data"""
        self._update_overview_tab()
        self._update_templates_tab()
        self._update_errors_tab()
        self.update_trend_chart()

    def _update_overview_tab(self):
        """Update overview tab data"""
        # Get time range for chart data
        {"Last 24 Hours": 1, "Last Week": 7, "Last Month": 30}[
            self.time_range.currentText()
        ]

        # Update performance chart
        self.performance_figure.clear()
        ax = self.performance_figure.add_subplot(111)

        # Get performance data
        chart_data = self.analytics.generate_performance_chart("processing_time")
        if chart_data:
            img = plt.imread(chart_data)
            ax.imshow(img)
            ax.axis("off")

        self.performance_canvas.draw()

    def _update_templates_tab(self):
        """Update templates tab data"""
        # Get template statistics
        stats = self.analytics.get_template_statistics()

        # Update table
        self.template_table.setRowCount(len(stats))
        for i, stat in enumerate(stats):
            self.template_table.setItem(i, 0, QTableWidgetItem(stat["template_type"]))
            self.template_table.setItem(
                i, 1, QTableWidgetItem(str(stat["document_count"]))
            )
            self.template_table.setItem(
                i, 2, QTableWidgetItem(f"{stat['average_processing_time']:.2f}")
            )
            self.template_table.setItem(
                i, 3, QTableWidgetItem(f"{stat['average_confidence']:.1f}")
            )
            self.template_table.setItem(
                i, 4, QTableWidgetItem(f"{stat['cache_hit_rate']:.1f}")
            )

        # Update comparison chart
        self.template_figure.clear()
        ax = self.template_figure.add_subplot(111)

        templates = [s["template_type"] for s in stats]
        times = [s["average_processing_time"] for s in stats]

        ax.bar(templates, times)
        ax.set_title("Processing Time by Template")
        ax.set_xlabel("Template Type")
        ax.set_ylabel("Average Processing Time (s)")
        plt.xticks(rotation=45)

        self.template_canvas.draw()

    def _update_errors_tab(self):
        """Update errors tab data"""
        # Get error statistics
        errors = self.analytics.get_error_analysis()

        # Update table
        self.error_table.setRowCount(len(errors))
        for i, error in enumerate(errors):
            self.error_table.setItem(i, 0, QTableWidgetItem(error["template_type"]))
            self.error_table.setItem(i, 1, QTableWidgetItem(str(error["total_errors"])))
            self.error_table.setItem(
                i, 2, QTableWidgetItem(str(error["total_documents"]))
            )
            self.error_table.setItem(
                i, 3, QTableWidgetItem(f"{error['error_rate']:.1f}")
            )

        # Update error distribution chart
        self.error_figure.clear()
        ax = self.error_figure.add_subplot(111)

        templates = [e["template_type"] for e in errors]
        rates = [e["error_rate"] for e in errors]

        ax.bar(templates, rates, color="red")
        ax.set_title("Error Rates by Template")
        ax.set_xlabel("Template Type")
        ax.set_ylabel("Error Rate (%)")
        plt.xticks(rotation=45)

        self.error_canvas.draw()

    def update_trend_chart(self):
        """Update trend analysis chart"""
        metric = self.metric_selector.currentText().lower().replace(" ", "_")

        self.trend_figure.clear()
        ax = self.trend_figure.add_subplot(111)

        # Get trend data
        chart_data = self.analytics.generate_performance_chart(metric)
        if chart_data:
            img = plt.imread(chart_data)
            ax.imshow(img)
            ax.axis("off")

        self.trend_canvas.draw()

"""Compact combined speed + RPM gauge panel.

Widgets:
    CompactSpeedDriveGauges: Vertically stacks SpeedGaugeWidget and DriveGaugeWidget
        under a single "Driving Data" header.
"""

# Import base widget classes for composing the combined panel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
# Import Qt enums for alignment constants
from PySide6.QtCore import Qt

# Import the speed arc-gauge component for the speedometer section
from ui.components.speed_gauge import SpeedGaugeWidget
# Import the RPM gauge panel for the tachometer section
from ui.panels.drive_panel import DriveGaugeWidget


class CompactSpeedDriveGauges(QWidget):
    """Vertically stacked speed and RPM gauge panels under a single header."""

    # Compose the speed gauge and RPM gauge into one panel with a shared header
    def __init__(self, index=0, parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Create the speed gauge sub-widget
        self._speed = SpeedGaugeWidget(index)
        # Create the RPM gauge sub-widget
        self._drive = DriveGaugeWidget(index)

        # Main vertical layout for the combined panel
        layout = QVBoxLayout(self)
        # Micro-padding around the panel edges
        layout.setContentsMargins(4, 4, 4, 4)
        # Moderate spacing between the header, speed gauge, separator, and RPM gauge
        layout.setSpacing(8)

        # Panel header identifying this combined section
        header = QLabel("Driving Data")
        # Shared panel-title styling
        header.setObjectName("PanelTitle")
        # Center the header
        header.setAlignment(Qt.AlignCenter)
        # Add the header at the top
        layout.addWidget(header)
        # Add the speed gauge below the header (stretch=1 to fill available space)
        layout.addWidget(self._speed, 1)
        # Create a thin horizontal separator between speed and RPM gauges
        sep = QFrame()
        sep.setObjectName("ValueSeparator")
        # Add the separator
        layout.addWidget(sep)
        # Add the RPM gauge below the separator (stretch=1)
        layout.addWidget(self._drive, 1)
        # Finalize the layout
        self.setLayout(layout)

    # Called every tick to forward fresh telemetry data to both sub-gauges
    def update_from_data(self, d):
        """Forward DisplayData to both speed and drive sub-widgets."""
        # Update the speed gauge with the latest speed data
        self._speed.update_from_data(d)
        # Update the RPM gauge with the latest RPM data
        self._drive.update_from_data(d)

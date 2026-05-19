"""RPM gauge panel using the shared TempMetricBlock.

Widgets:
    DriveGaugeWidget: Displays engine RPM with animated bar and AVG/MIN/MAX stats.
"""

# Import the base widget class and vertical layout for composing the panel
from PySide6.QtWidgets import QWidget, QVBoxLayout
# Import Qt constants (used implicitly via TempMetricBlock or future alignment needs)
from PySide6.QtCore import Qt

# Reuse TempMetricBlock so RPM gets the same animated bar + stats pattern as temperature
from ui.panels.temperature_panel import TempMetricBlock


class DriveGaugeWidget(QWidget):
    """RPM gauge panel using a TempMetricBlock with animated bar and stats."""

    # Build the RPM panel with a single TempMetricBlock wrapped in a vertical layout
    def __init__(self, index=0, parent=None):
        # Initialize QWidget so Qt properly registers this panel
        super().__init__(parent)
        # Store the grid index for identification by any parent layout
        self._index = index
        # Create a vertical layout as the panel's single-axis arrangement
        layout = QVBoxLayout(self)
        # Micro-padding to keep the contents away from panel borders
        layout.setContentsMargins(4, 4, 4, 4)
        # Minimal spacing since there is only one child widget
        layout.setSpacing(2)

        # Create the RPM metric block with green accent, 0-8000 RPM range
        self._gauge = TempMetricBlock("rpm", "RPM", min_val=0, max_val=8000, unit="RPM", accent_color="#00ffa6")
        # Add the gauge block to fill the panel with stretch=1
        layout.addWidget(self._gauge, 1)
        # Commit the layout to this widget
        self.setLayout(layout)

    # Called every tick to refresh the RPM display from fresh telemetry data
    def update_from_data(self, d):
        """Update RPM value and AVG/MIN/MAX stats from a DisplayData object."""
        # Push the latest RPM value into the animated TempMetricBlock
        self._gauge.update_value(d.rpm)
        # Update the RPM AVG/MIN/MAX stats with one-decimal formatting
        self._gauge.update_stats(f"{d.rpm_avg:.1f}", f"{d.rpm_min:.1f}", f"{d.rpm_max:.1f}")

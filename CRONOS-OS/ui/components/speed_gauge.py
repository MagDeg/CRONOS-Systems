"""Speed gauge panel using the shared TempMetricBlock.

Widgets:
    SpeedGaugeWidget: Displays velocity (km/h) with animated bar and AVG/MIN/MAX stats.
"""

# Import QWidget as the base class and QVBoxLayout to stack the gauge vertically
from PySide6.QtWidgets import QWidget, QVBoxLayout
# Import Qt for alignment flags used internally by child widgets
from PySide6.QtCore import Qt

# Import the reusable metric block that draws the animated bar and stat labels
from ui.panels.temperature_panel import TempMetricBlock


class SpeedGaugeWidget(QWidget):
    """Speed gauge panel using a TempMetricBlock with animated bar and stats."""

    def __init__(self, index=0, parent=None):
        # Initialize the QWidget base so the widget is properly registered in Qt's parent-child tree
        super().__init__(parent)
        # Store the index so this widget can be identified in a list of gauges (e.g. left/mid/right)
        self._index = index
        # Create a vertical layout to hold the TempMetricBlock
        layout = QVBoxLayout(self)
        # Tight margins so the gauge hugs its container with minimal wasted space
        layout.setContentsMargins(4, 4, 4, 4)
        # Minimal spacing between the bar and any potential adjacent elements
        layout.setSpacing(2)

        # Build the actual gauge block: configures the label, range, unit, and cyan accent color matching the HUD theme
        self._gauge = TempMetricBlock("speed", "Speed", min_val=0, max_val=200, unit="km/h", accent_color="#00d4ff")
        # Insert the gauge into the layout with stretch factor 1 so it fills available space
        layout.addWidget(self._gauge, 1)
        # Attach the layout to self so Qt knows how to arrange children
        self.setLayout(layout)

    def update_from_data(self, d):
        """Update velocity (km/h) and AVG/MIN/MAX stats from a DisplayData object."""
        # Push the latest velocity into the gauge's animated bar
        self._gauge.update_value(d.velocity)
        # Refresh the three stat readouts below the bar with formatted one-decimal values
        self._gauge.update_stats(f"{d.velocity_avg:.1f}", f"{d.velocity_min:.1f}", f"{d.velocity_max:.1f}")

"""Trip computer popup showing distance, speeds, and time breakdowns.

Widgets:
    TripPopup: Dialog with a 2x3 grid of trip metrics (distance, avg/max speed,
        moving/stopped/total time).
"""

# Import QDialog as popup base, layout classes for grid/stacking,
# QPushButton for close, QLabel/Frame for text and separators, QGridLayout for the 2x3 block grid
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QGridLayout
# Import Qt namespace for alignment constants (AlignCenter) used on labels
from PySide6.QtCore import Qt


class _TripBlock(QFrame):
    """Single trip-metric block with label, value, and unit."""

    def __init__(self, label, unit, parent=None):
        # Init QFrame as the container so each metric gets a styled rectangular card
        super().__init__(parent)
        # Object name for QSS targeting by #MetricBlock rules in the stylesheet
        self.setObjectName("MetricBlock")
        # Vertical layout stacks label, value, and unit vertically inside the card
        layout = QVBoxLayout(self)
        # Tight padding so the three text lines feel grouped together
        layout.setContentsMargins(10, 6, 10, 6)
        # Minimal spacing between label/value/unit for a compact readout
        layout.setSpacing(2)
        # Value label starts as a dash — replaced by set_text when real data arrives
        self._val = QLabel("-")
        # Apply the global MetricValue style for large, prominent numbers
        self._val.setObjectName("MetricValue")
        # Center the numeric value horizontally within the card
        self._val.setAlignment(Qt.AlignCenter)
        # Unit label shows the measurement dimension (e.g. "km", "km/h", "")
        u = QLabel(unit)
        # Apply the global MetricUnit style for smaller, muted unit text
        u.setObjectName("MetricUnit")
        u.setAlignment(Qt.AlignCenter)
        # Label at the top tells the user what this metric is (e.g. "Distance")
        lbl = QLabel(label)
        # Apply the global MetricLabel style for the category name
        lbl.setObjectName("MetricLabel")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        layout.addWidget(self._val)
        layout.addWidget(u)
        # Explicitly assign the layout so QFrame manages it properly
        self.setLayout(layout)

    def set_text(self, t):
        # Update the value label text when new trip data arrives from the calculator
        self._val.setText(t)


class TripPopup(QDialog):
    """Dialog showing trip computer metrics: distance, avg/max speed, moving/stopped/total time."""

    def __init__(self, parent=None):
        # Init QDialog so this works as a standard popup dialog
        super().__init__(parent)
        # Window title so the OS identifies this as the trip computer view
        self.setWindowTitle("Trip Computer")
        # Fixed size keeps the grid tidy and prevents ugly layout stretching
        self.setFixedSize(360, 440)
        # Object name for QSS targeting via #TripPopup
        self.setObjectName("TripPopup")

        # Root vertical layout stacks header, separator, grid, separator, close button
        layout = QVBoxLayout(self)
        # Moderate margins so the dark background shows as a border
        layout.setContentsMargins(12, 12, 12, 12)
        # Compact spacing between header/grid/footer sections
        layout.setSpacing(8)

        # Header label identifying this as the trip computer view
        header = QLabel("Trip Computer")
        # Apply the global PanelTitle QSS for a consistent header look
        header.setObjectName("PanelTitle")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Separator between header and the 2x3 metric grid
        sep = QFrame(objectName="ValueSeparator")
        layout.addWidget(sep)

        # Grid layout arranges the 6 metric blocks in 3 rows × 2 columns
        grid = QGridLayout()
        grid.setSpacing(8)

        # Six trip metric blocks, each following the label/value/unit pattern
        self._dist = _TripBlock("Distance", "km")
        self._avg = _TripBlock("Avg Speed", "km/h")
        self._max = _TripBlock("Max Speed", "km/h")
        self._moving = _TripBlock("Moving Time", "")
        self._stopped = _TripBlock("Stopped Time", "")
        self._total = _TripBlock("Total Time", "")

        # Place each block in the grid: (row, col)
        grid.addWidget(self._dist, 0, 0)     # top-left
        grid.addWidget(self._avg, 0, 1)      # top-right
        grid.addWidget(self._max, 1, 0)      # middle-left
        grid.addWidget(self._moving, 1, 1)   # middle-right
        grid.addWidget(self._stopped, 2, 0)  # bottom-left
        grid.addWidget(self._total, 2, 1)    # bottom-right

        # Stretch factor 1 lets the grid expand to fill available space above the button row
        layout.addLayout(grid, 1)

        sep2 = QFrame(objectName="ValueSeparator")
        layout.addWidget(sep2)

        # Standard centered close-button row, same pattern as other popups
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        b = QPushButton("Close")
        b.setObjectName("SettingsButton")
        b.setFixedWidth(100)
        b.clicked.connect(self.accept)
        btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Inline stylesheet for the dark theme background; single-line QSS for brevity
        self.setStyleSheet("#TripPopup{background-color:#050814;}")

    def _fmt_time(self, ms):
        # Convert milliseconds to H:MM:SS format for human-readable time readouts
        if ms <= 0:
            return "0:00"
        s = int(round(ms / 1000))
        h, r = divmod(s, 3600)
        m, sec = divmod(r, 60)
        return f"{h}:{m:02d}:{sec:02d}"

    def update_from_data(self, d):
        """Update all trip metrics from a DisplayData object."""
        # Push each calculated trip value into its corresponding _TripBlock widget
        self._dist.set_text(f"{d.distance:.2f}")
        self._avg.set_text(f"{d.avg_speed:.1f}")
        self._max.set_text(f"{d.max_speed:.1f}")
        self._moving.set_text(self._fmt_time(d.moving_time_ms))
        self._stopped.set_text(self._fmt_time(d.stopped_time_ms))
        # Total time is simply the sum of moving and stopped durations
        self._total.set_text(self._fmt_time(d.moving_time_ms + d.stopped_time_ms))

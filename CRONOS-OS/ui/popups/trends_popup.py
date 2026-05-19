"""Historical sensor-trend sparklines popup.

Widgets:
    TrendsPopup: Dialog showing compact QPainter sparklines for battery voltage,
        battery %, engine temp, battery temp, and chip temp.
"""

# Import Qt dialog/layout/widget base classes and the QPushButton for the close action,
# QLabel for the title, QFrame for separators
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
# Import Qt enums for alignment and rectangle/point types for QPainter positioning
from PySide6.QtCore import Qt, QRectF, QPointF
# Import QPainter for custom widget painting, QColor/QPen for line styling, QFont for text rendering
from PySide6.QtGui import QPainter, QColor, QPen, QFont

# Import the shared ring-buffer history object that all sparklines read from
from data.metric_history import history


class _Sparkline(QFrame):
    """Compact QPainter-drawn sparkline for a single metric history."""

    def __init__(self, label, keys, color="#00d4ff", min_val=0, max_val=100, unit="", parent=None):
        # Init QFrame as the canvas widget for this sparkline
        super().__init__(parent)
        # Human-readable label shown at the top-left of the sparkline (e.g. "Battery Voltage")
        self._label = label
        # The metric key(s) in the history dict — single key or list, stored for paintEvent
        self._keys = keys
        # Parse the hex color string into a QColor object once, so paintEvent doesn't re-parse it
        self._color = QColor(color)
        # Minimum expected value for the Y-axis, used to normalize the sparkline
        self._min_v = min_val
        # Maximum expected value for the Y-axis, used to normalize the sparkline
        self._max_v = max_val
        # Unit string appended to the last-value annotation (e.g. "V", "%", "°C")
        self._unit = unit
        # Enforce a minimum width/height so the sparkline doesn't collapse to nothing
        self.setMinimumSize(160, 80)

    def paintEvent(self, event):
        """Paint the sparkline background, label, dashed midline, and data line from history."""
        p = QPainter(self)
        # Enable anti-aliasing so the sparkline lines are smooth, not jagged
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # Fill the entire widget area with the dark background color
        p.fillRect(0, 0, w, h, QColor(5, 10, 30))

        # Set a bold 10pt Segoe UI font for the label
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        # Cyan color for the label text to match the HUD theme
        p.setPen(QColor(0, 191, 255))
        # Draw the label at the top-left with a small inset margin
        p.drawText(QRectF(6, 4, w - 12, 18), Qt.AlignLeft, self._label)

        # Margin around the plot area so the line doesn't clip at widget edges
        margin = 4
        # Define the plot rectangle: leaves room for label at top, margin on other sides
        plot_r = QRectF(margin, 22, w - 2 * margin, h - 26 - margin)
        # Draw a dashed horizontal line at the vertical midpoint as a reference guide
        p.setPen(QPen(QColor(0, 191, 255, 20), 1, Qt.DashLine))
        mid_y = plot_r.top() + plot_r.height() / 2
        p.drawLine(QPointF(plot_r.left(), mid_y), QPointF(plot_r.right(), mid_y))

        # If no metric keys are configured, there's nothing to plot — early exit
        if not self._keys:
            return

        # Extract the first key (handles both bare string keys and lists of keys)
        first_key = self._keys[0] if isinstance(self._keys, list) else self._keys
        # Fetch the timestamps and data values for this key from the shared ring buffer
        ts, data_dict = history.get([first_key])
        vals = data_dict.get(first_key, [])
        # Need at least 2 data points to draw a line
        if len(vals) < 2 or len(ts) < 2:
            return
        # Zip timestamps with values to create ordered (x, y) pairs for plotting
        pts = list(zip(ts, vals))

        # Cap the number of plotted points to 150 to keep paintEvent fast
        max_pts = 150
        if len(pts) > max_pts:
            pts = pts[-max_pts:]

        rng = self._max_v - self._min_v
        if rng <= 0:
            rng = 1

        path = []
        for i, (t, v) in enumerate(pts):
            # Clamp the value to the configured min/max range so outliers don't break the chart
            v = max(self._min_v, min(self._max_v, v))
            # Map the data-point index linearly to the plot rectangle's X range
            x = plot_r.left() + plot_r.width() * i / (len(pts) - 1)
            # Map the clamped value inversely to the plot rectangle's Y range (Y grows downward)
            y = plot_r.bottom() - plot_r.height() * (v - self._min_v) / rng
            path.append(QPointF(x, y))

        # Draw the sparkline as a series of connected line segments
        p.setPen(QPen(self._color, 1.5))
        for i in range(1, len(path)):
            p.drawLine(path[i - 1], path[i])

        # If we have at least one point, annotate the last value at the top-right of the plot area
        if path:
            last_v = pts[-1][1]
            p.setFont(QFont("Segoe UI", 9))
            p.setPen(self._color)
            # Draw the latest value with its unit in the top-right corner of the plot rectangle
            p.drawText(QRectF(plot_r.left(), plot_r.top() - 2, plot_r.width(), 16),
                       Qt.AlignRight, f"{last_v:.1f} {self._unit}")


class TrendsPopup(QDialog):
    """Dialog showing multiple compact sparkline trends for battery, temps, and chip."""

    def __init__(self, parent=None):
        # Init QDialog so this works as a standard popup window
        super().__init__(parent)
        # Window title for OS taskbar identification
        self.setWindowTitle("Sensor Trends")
        # Fixed size keeps the five sparklines laid out predictably
        self.setFixedSize(540, 540)
        # Object name for QSS targeting via #TrendsPopup
        self.setObjectName("TrendsPopup")

        # Root vertical layout stacks header, separator, sparklines, separator, close button
        layout = QVBoxLayout(self)
        # Tight margins — the dark background acts as the border
        layout.setContentsMargins(12, 12, 12, 12)
        # Minimal spacing between sparklines for a dense dashboard feel
        layout.setSpacing(6)

        # Header so the user knows this is the sensor trends overview
        header = QLabel("Sensor Trends")
        header.setObjectName("PanelTitle")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        sep = QFrame(objectName="ValueSeparator")
        layout.addWidget(sep)

        # Define the five sparklines: battery voltage, battery %, engine temp, battery temp, chip temp
        # Each configured with its own label, history key, line color, expected min/max, and unit
        self._sparks = [
            _Sparkline("Battery Voltage", "voltage_battery", "#00d4ff", 10, 14, "V"),
            _Sparkline("Battery %", "battery_pct", "#00ff88", 0, 100, "%"),
            _Sparkline("Engine Temp", "temperature_engine", "#ff7f50", 0, 120, "°C"),
            _Sparkline("Battery Temp", "temperature_battery", "#ffa726", 0, 60, "°C"),
            _Sparkline("Chip Temp", "temperature_chip", "#ff5050", 0, 90, "°C"),
        ]

        for s in self._sparks:
            # Stretch factor 1 distributes vertical space equally among all sparklines
            layout.addWidget(s, 1)
            # Separator between each sparkline for visual distinction
            layout.addWidget(QFrame(objectName="ValueSeparator"))

        # Standard centered close-button layout, same pattern as other popups
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        b = QPushButton("Close")
        b.setObjectName("SettingsButton")
        b.setFixedWidth(100)
        b.clicked.connect(self.accept)
        btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Inline dark-background style for the HUD theme
        self.setStyleSheet("#TrendsPopup{background-color:#050814;}")

    def update_trends(self):
        """Trigger repaint of all embedded sparkline widgets."""
        # Calling update() on each sparkline queues a paintEvent so the sparklines redraw with new data
        for s in self._sparks:
            s.update()

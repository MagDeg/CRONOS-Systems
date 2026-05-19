"""Network connection status, packet-loss, and delay sparkline display.

Widgets:
    CombinedNetworkPanel: Panel showing packet-loss %, a delay sparkline, and connection
        status indicator.
"""

# Import all Qt widgets needed for the network panel's composite UI
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
# Import Qt enums and timer for layout constants and animation loops
from PySide6.QtCore import Qt, QTimer, QPointF
# Import painting primitives for the custom sparkline widget
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush
# Import deque as a fixed-length ring buffer for the sparkline's recent-value history
from collections import deque
# Import datetime to stamp the last-check time on the connection status
from datetime import datetime


class _Sparkline(QWidget):
    """Smooth animated sparkline widget for delay history."""

    # Initialize with default values, a ring buffer, and an animation timer
    def __init__(self, parent=None):
        # Properly initialize the QWidget base class
        super().__init__(parent)
        # Ring buffer seeded with 20 zeros; holds up to 50 entries for a rolling window
        self._values = deque([0] * 20, maxlen=50)
        # Fixed height so the sparkline always occupies the same vertical space
        self.setFixedHeight(50)
        # Current smooth-animation position (starts at zero)
        self._smooth = 0.0
        # Target that the animator converges on each tick
        self._target = 0.0
        # 60fps animation timer for smooth value transitions
        self._anim = QTimer(self)
        # Connect timer ticks to the private smoothing method
        self._anim.timeout.connect(self._tick)
        # Start the animation loop immediately
        self._anim.start(16)

    # Single animation tick: smoothly move _smooth toward _target, then repaint
    def _tick(self):
        # Compute remaining distance to the target
        diff = self._target - self._smooth
        # Snap to target when very close to eliminate visible jitter
        if abs(diff) < 0.05:
            self._smooth = self._target
        else:
            # Move 25% of the gap per frame for a smooth but responsive ease
            self._smooth += diff * 0.25
        # Trigger a repaint so the canvas reflects the new smooth value
        self.update()

    # Append a new value to the ring buffer and set it as the animation target
    def push(self, v):
        """Append a new value; trigger repaint via animation."""
        # The animator will smoothly ramp from wherever it is to this new target
        self._target = float(v)
        # Add the raw value to the deque ring buffer for painting
        self._values.append(float(v))

    # Qt paint event: render a cubic Hermite-spline sparkline of the delay history
    def paintEvent(self, event):
        """Draw a cubic-spline sparkline of the recent delay values."""
        # Create a QPainter for this widget's canvas
        p = QPainter(self)
        # Enable anti-aliasing for smooth curves
        p.setRenderHint(QPainter.Antialiasing)
        # Enable smooth pixmap transform to avoid pixel snapping artifacts
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        # Cache the current width and height for coordinate calculations
        w, h = self.width(), self.height()
        # Bail out early if there aren't enough points to draw a meaningful line
        if len(self._values) < 2 or w < 10:
            return
        # Snapshot the ring buffer into a list for random access
        vals = list(self._values)
        # Replace the last raw value with the smoothed value for a clean endpoint
        vals[-1] = self._smooth
        # Find the min and max for vertical normalization
        mn, mx = min(vals), max(vals)
        # Guard against zero range to avoid division by zero
        rng = mx - mn if mx != mn else 1
        # Map each value to an (x, y) point, fitting the curve into the widget rect
        pts = [QPointF(i * w / (len(vals) - 1), h - (v - mn) / rng * (h - 4) - 2) for i, v in enumerate(vals)]
        # Build a smooth path using Catmull-Rom-like cubic Hermite spline interpolation
        path = QPainterPath()
        # Start the path at the first point
        path.moveTo(pts[0])
        # Iterate through each segment, computing control points for cubic Bézier curves
        for i in range(len(pts) - 1):
            p0 = pts[i]
            p3 = pts[i + 1]
            # Compute first control point using the previous point for tangent continuity
            if i > 0:
                c1 = QPointF(p0.x() + (p3.x() - pts[i - 1].x()) / 6, p0.y() + (p3.y() - pts[i - 1].y()) / 6)
            else:
                # At the first point, fall back to a simple forward-tangent estimate
                c1 = QPointF(p0.x() + (p3.x() - p0.x()) / 3, p0.y())
            # Compute second control point using the next point for tangent continuity
            if i < len(pts) - 2:
                c2 = QPointF(p3.x() - (pts[i + 2].x() - p0.x()) / 6, p3.y() - (pts[i + 2].y() - p0.y()) / 6)
            else:
                # At the last point, fall back to a simple backward-tangent estimate
                c2 = QPointF(p3.x() - (p3.x() - p0.x()) / 3, p3.y())
            # Draw a cubic Bézier segment from p0 to p3 using the computed control points
            path.cubicTo(c1, c2, p3)
        # Set the pen to a bright cyan, thin line with rounded ends and joins
        p.setPen(QPen(QColor("#00aaff"), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        # Render the complete spline path onto the widget
        p.drawPath(path)
        # Release the painter to clean up resources
        p.end()


class _StatusIndicator(QWidget):
    """Connection status indicator with colored dot and detail text."""

    # Build a vertical layout showing connection status, a colored dot, and a last-check timestamp
    def __init__(self, parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Initial state is disconnected until the data layer reports otherwise
        self._status = "disconnected"
        # Start with a red color for the disconnected state
        self._color = QColor("#ff4d4f")
        # Main vertical layout for the status indicator block
        layout = QVBoxLayout(self)
        # Center all children vertically
        layout.setAlignment(Qt.AlignCenter)
        # Heading label identifying this section
        lbl = QLabel("Connection Status")
        # Use the shared metric-label styling
        lbl.setObjectName("MetricLabel")
        # Center the heading horizontally
        lbl.setAlignment(Qt.AlignCenter)
        # Add the heading to the layout
        layout.addWidget(lbl)

        # Create the colored dot that visually indicates connection state
        self._dot = QLabel()
        # Fixed 14×14 pixel circle for the status dot
        self._dot.setFixedSize(14, 14)
        # CSS class that will apply the circular shape via border-radius
        self._dot.setObjectName("StatusDot")
        # Text label showing the human-readable status name
        self._text = QLabel("Disconnected")
        # Use the large metric-value font for the status text
        self._text.setObjectName("MetricValue")
        # Center the status text
        self._text.setAlignment(Qt.AlignCenter)

        # Horizontal row holding the dot and text side by side
        dot_row = QHBoxLayout()
        # Elastic spacer on the left to center the dot+text group
        dot_row.addStretch()
        # Add the colored dot
        dot_row.addWidget(self._dot)
        # Add the status text immediately after the dot
        dot_row.addWidget(self._text)
        # Elastic spacer on the right to keep the group centered
        dot_row.addStretch()
        # Attach the dot+text row to the main vertical layout
        layout.addLayout(dot_row)

        # Detail line showing when the last connection check occurred
        self._detail = QLabel("Last Check: -")
        # Use a smaller, muted font for the detail line
        self._detail.setObjectName("DetailText")
        # Center the detail text
        self._detail.setAlignment(Qt.AlignCenter)
        # Add the detail line at the bottom of the block
        layout.addWidget(self._detail)
        # Finalize the layout
        self.setLayout(layout)

    # Update the displayed status text and the dot's color
    def set_status(self, status: str, lamp_color: str):
        """Set connection status text and dot color (hex)."""
        # Persist the status string for any internal checks
        self._status = status
        # Convert the hex color string to a QColor for potential future use
        self._color = QColor(lamp_color)
        # Display the capitalized status (e.g. "Connected")
        self._text.setText(status.capitalize())
        # Apply the dot color via inline stylesheet with border-radius to make it circular
        self._dot.setStyleSheet(
            f"background: {lamp_color}; border-radius: 7px; min-width: 14px; min-height: 14px;"
        )

    # Update the detail text line (typically the "Last Check: HH:MM:SS" timestamp)
    def set_detail(self, text: str):
        """Set the detail line (e.g. last check timestamp)."""
        self._detail.setText(text)


class _PacketLossBlock(QWidget):
    """Animated packet-loss % block with AVG/MIN/MAX stats."""

    # Build a block showing packet-loss percentage with a color-coded animated bar
    def __init__(self, parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Smooth position for the value text animation
        self._smooth = 0.0
        # Target for the value text animator to converge on
        self._target = 0.0
        # Smooth position for the progress bar animation
        self._bar_pct = 0.0

        # Main vertical layout for this block
        layout = QVBoxLayout(self)
        # Horizontal gutters with minimal vertical padding
        layout.setContentsMargins(10, 2, 10, 2)
        # No spacing between stacked rows
        layout.setSpacing(0)

        # Label identifying this metric as "Packet Loss"
        lbl = QLabel("Packet Loss")
        # Shared metric-label styling
        lbl.setObjectName("MetricLabel")
        # Attach the label to the layout
        layout.addWidget(lbl)

        # Horizontal row for the percentage value and unit
        val_row = QHBoxLayout()
        # Label showing the current packet-loss percentage
        self._value = QLabel("0.0")
        # Large-value font styling
        self._value.setObjectName("MetricValue")
        # Unit label showing "%"
        self._unit = QLabel("%")
        # Smaller-dimension styling for the unit
        self._unit.setObjectName("MetricUnit")
        # Left spacer to center the value+unit pair
        val_row.addStretch()
        # Add the numeric value
        val_row.addWidget(self._value)
        # Add the percent sign immediately after
        val_row.addWidget(self._unit)
        # Right spacer to complete centering
        val_row.addStretch()
        # Attach the value row
        layout.addLayout(val_row)

        # Progress bar that visually represents the packet-loss level
        self._bar = QProgressBar()
        # Use the temperature-bar styling for consistency
        self._bar.setObjectName("TempBar")
        # Internal 0-100 percentage range
        self._bar.setRange(0, 100)
        # Start at zero; animator fills it in
        self._bar.setValue(0)
        # Hide the default percentage text
        self._bar.setTextVisible(False)
        # Thin 8px bar to keep the block compact
        self._bar.setFixedHeight(8)
        # Add the bar below the value row
        layout.addWidget(self._bar)

        # Horizontal row for AVG/MIN/MAX stats
        stats_row = QHBoxLayout()
        # Tight margins between stat boxes
        stats_row.setContentsMargins(2, 0, 2, 0)
        # Create stat value labels with defaults and shared styling
        self._avg = QLabel("-", objectName="StatValue", alignment=Qt.AlignCenter)
        self._min = QLabel("-", objectName="StatValue", alignment=Qt.AlignCenter)
        self._max = QLabel("-", objectName="StatValue", alignment=Qt.AlignCenter)
        # Add labeled stat boxes in order
        stats_row.addWidget(self._stat_box("AVG", self._avg))
        stats_row.addWidget(self._stat_box("MIN", self._min))
        stats_row.addWidget(self._stat_box("MAX", self._max))
        # Attach the stats row
        layout.addLayout(stats_row)

        # 60fps animation timer for smooth value and bar transitions
        self._anim = QTimer(self)
        # Connect ticks to the smoothing method
        self._anim.timeout.connect(self._tick)
        # Start the animation loop
        self._anim.start(16)

        # Finalize the layout
        self.setLayout(layout)

    # Build a compact container with a stat label above a value
    def _stat_box(self, lbl, val):
        # Container widget for the stat label-value pair
        w = QWidget()
        # Vertical layout stacks label above value
        l = QVBoxLayout(w)
        # Tight margins for a compact layout
        l.setContentsMargins(2, 0, 2, 0)
        # No gap between the label and the value
        l.setSpacing(0)
        # Add the stat name label (e.g. "AVG") centered
        l.addWidget(QLabel(lbl, objectName="StatLabel", alignment=Qt.AlignCenter))
        # Add the numeric value label below
        l.addWidget(val)
        # Return the assembled box
        return w

    # Animation tick: smooth both the value text and the progress bar position
    def _tick(self):
        # Calculate distance to the target value
        diff = self._target - self._smooth
        # Snap to target when close to avoid jitter
        if abs(diff) < 0.05:
            self._smooth = self._target
        else:
            # Move 20% of the gap per frame for smooth easing
            self._smooth += diff * 0.2
        # Update the displayed percentage with one decimal place
        self._value.setText(f"{self._smooth:.1f}")

        # Calculate the bar-position gap separately for independent smoothing
        bar_diff = self._smooth - self._bar_pct
        # Snap the bar when close to the target to avoid twitching
        if abs(bar_diff) < 0.1:
            self._bar_pct = self._smooth
        else:
            # Move the bar 20% of the remaining gap per frame
            self._bar_pct += bar_diff * 0.2
        # Update the progress bar with the integer position
        self._bar.setValue(int(self._bar_pct))
        # Default bar color is green (low packet loss)
        c = QColor("#2ecc71")
        # Switch to amber/yellow when packet loss exceeds 50%
        if self._bar_pct > 50:
            c = QColor("#ffb432")
        # Switch to red when packet loss exceeds 75% (critical)
        if self._bar_pct > 75:
            c = QColor("#ff5050")
        # Apply the dynamic color via an inline stylesheet
        self._bar.setStyleSheet(
            f"QProgressBar::chunk {{ background: {c.name()}; border-radius: 4px; }}"
        )

    # Receive a new packet-loss value; the animator will converge to it
    def update_value(self, val, color="#2ecc71"):
        """Set target packet-loss %; smooth animator converges on it."""
        self._target = float(val)

    # Receive fresh AVG/MIN/MAX stats and push them into the stat labels
    def update_stats(self, avg, mn, mx):
        self._avg.setText(avg if avg is not None else "-")
        self._min.setText(mn if mn is not None else "-")
        self._max.setText(mx if mx is not None else "-")


class _DelayBlock(QWidget):
    """Delay display with sparkline chart and AVG/MIN/MAX stats."""

    # Build a block showing current delay, a sparkline history, and stats
    def __init__(self, parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Main vertical layout for the delay block
        layout = QVBoxLayout(self)
        # Horizontal padding with minimal vertical spacing
        layout.setContentsMargins(10, 2, 10, 2)
        # No spacing between stacked rows
        layout.setSpacing(0)

        # Label identifying this metric as "Delay"
        lbl = QLabel("Delay")
        # Shared metric-label styling
        lbl.setObjectName("MetricLabel")
        # Attach the label
        layout.addWidget(lbl)

        # Custom sparkline widget showing the recent delay history as a smooth curve
        self._sparkline = _Sparkline()
        # Add the sparkline below the label
        layout.addWidget(self._sparkline)

        # Current delay value label (e.g. "42 ms")
        self._value = QLabel("0 ms")
        # Large-value font styling
        self._value.setObjectName("MetricValue")
        # Center the delay value below the sparkline
        self._value.setAlignment(Qt.AlignCenter)
        # Add the value label
        layout.addWidget(self._value)

        # Horizontal row for AVG/MIN/MAX stats
        stats_row = QHBoxLayout()
        # Tight margins between stat boxes
        stats_row.setContentsMargins(2, 0, 2, 0)
        # Create stat labels with defaults and shared styling
        self._avg = QLabel("-", objectName="StatValue", alignment=Qt.AlignCenter)
        self._min = QLabel("-", objectName="StatValue", alignment=Qt.AlignCenter)
        self._max = QLabel("-", objectName="StatValue", alignment=Qt.AlignCenter)
        # Add labeled stat boxes in order
        stats_row.addWidget(self._stat_box("AVG", self._avg))
        stats_row.addWidget(self._stat_box("MIN", self._min))
        stats_row.addWidget(self._stat_box("MAX", self._max))
        # Attach the stats row
        layout.addLayout(stats_row)

        # Finalize the layout
        self.setLayout(layout)

    # Build a compact stat label-value container
    def _stat_box(self, lbl, val):
        # Container for the label-value pair
        w = QWidget()
        # Vertical layout
        l = QVBoxLayout(w)
        # Tight margins
        l.setContentsMargins(2, 0, 2, 0)
        # No gap between the label and value
        l.setSpacing(0)
        # Add the stat name label
        l.addWidget(QLabel(lbl, objectName="StatLabel", alignment=Qt.AlignCenter))
        # Add the numeric value below
        l.addWidget(val)
        # Return the assembled box
        return w

    # Push a new delay value into the sparkline and update the current-value display
    def update_value(self, val):
        """Push a delay value (ms) into the sparkline and update text."""
        # Feed the value into the sparkline's ring buffer and animator
        self._sparkline.push(val)
        # Display the current delay as an integer with "ms" suffix
        self._value.setText(f"{val:.0f} ms")

    # Receive fresh AVG/MIN/MAX delay stats and push them into the stat labels
    def update_stats(self, avg, mn, mx):
        self._avg.setText(avg if avg is not None else "-")
        self._min.setText(mn if mn is not None else "-")
        self._max.setText(mx if mx is not None else "-")


class CombinedNetworkPanel(QWidget):
    """Panel showing packet loss %, delay sparkline, and connection status."""

    # Compose the full network panel from packet-loss, delay, and status sub-widgets
    def __init__(self, index=0, parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Store the grid index for potential layout usage
        self._index = index

        # Main vertical layout for the panel
        layout = QVBoxLayout(self)
        # Micro-padding around the panel edges
        layout.setContentsMargins(4, 4, 4, 4)
        # Minimal spacing between the three subsections
        layout.setSpacing(2)

        # Panel title identifying this section
        header = QLabel("Network")
        # Shared panel-title styling
        header.setObjectName("PanelTitle")
        # Center the header
        header.setAlignment(Qt.AlignCenter)
        # Add the header at the top
        layout.addWidget(header)

        # Instantiate the three sub-widgets that form the network panel
        self._packet = _PacketLossBlock()
        self._delay = _DelayBlock()
        self._status = _StatusIndicator()

        # Factory that produces a thin horizontal separator frame
        def _sep():
            s = QFrame()
            s.setObjectName("ValueSeparator")
            return s

        # Add the packet-loss block as the first section (stretch=1)
        layout.addWidget(self._packet, 1)
        # Separate packet-loss from delay
        layout.addWidget(_sep())
        # Add the delay block as the second section (stretch=1)
        layout.addWidget(self._delay, 1)
        # Separate delay from the status indicator
        layout.addWidget(_sep())
        # Add the connection status as the third section (stretch=1)
        layout.addWidget(self._status, 1)
        # Vertically center the entire contents of the panel
        layout.setAlignment(Qt.AlignVCenter)
        # Finalize the layout
        self.setLayout(layout)

    # Called every tick to refresh all network metrics from fresh telemetry data
    def update_from_data(self, d):
        """Update packet loss, delay sparkline, and connection status from a DisplayData object."""
        # Push the latest packet-loss value into the animated block
        self._packet.update_value(d.packet_loss)
        # Update the packet-loss AVG/MIN/MAX stats with one-decimal formatting
        self._packet.update_stats(f"{d.packet_loss_avg:.1f}", f"{d.packet_loss_min:.1f}", f"{d.packet_loss_max:.1f}")
        # Push the latest delay value into the sparkline and delay display
        self._delay.update_value(float(d.delay))
        # Update the delay AVG/MIN/MAX stats with integer formatting
        self._delay.update_stats(f"{d.delay_avg:.0f}", f"{d.delay_min:.0f}", f"{d.delay_max:.0f}")
        # Determine connection state from the boolean flag
        if d.connection_state:
            # Green dot and "Connected" text when the link is active
            self._status.set_status("connected", "#2ecc71")
        else:
            # Red dot and "Disconnected" text when the link is down
            self._status.set_status("disconnected", "#ff4d4f")
        # Stamp the detail line with the current wall-clock time
        self._status.set_detail(f"Last Check: {datetime.now().strftime('%H:%M:%S')}")

    # Stub for backward compatibility with older callers
    def set_packet_stats(self, avg, mn, mx):
        pass

    # Manually push a single delay value into the delay display
    def set_delay_value(self, val):
        self._delay.update_value(val)

    # Manually set the detail text on the status indicator
    def set_detail(self, text):
        self._status.set_detail(text)


def combinedNetworkPanel(index, packet_loss, delay_values, connection_status, packet_stats, title, accent_color):
    return CombinedNetworkPanel(index)

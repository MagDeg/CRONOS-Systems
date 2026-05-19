"""Acceleration, G-force, distance, and estimated rounds display.

Widgets:
    AccelGForceDistance: Panel showing acceleration (m/s²), G-force (g), distance (km),
        and estimated rounds based on round-length setting.
"""

# Import core Qt widget classes used to compose the metric display blocks
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
# Import Qt constants and the timer class for layout alignment and animation
from PySide6.QtCore import Qt, QTimer
# Import QColor so progress bars can transition between colors dynamically at runtime
from PySide6.QtGui import QColor

# Import the temperature metric block so acceleration/G-force reuse its animated-bar + stats pattern
from ui.panels.temperature_panel import TempMetricBlock


class _PlainBlock(QWidget):
    """Non-temperature metric block with optional animated bar and AVG/MIN/MAX stats."""

    # Establish the block's identity, display values, and whether bar/stats are shown
    def __init__(self, metric, label, value, unit, accent_color="#00d4ff", show_stats=True, show_bar=False, bar_max=5, parent=None):
        # Chain to QWidget so Qt properly initializes this widget
        super().__init__(parent)
        # Tag this widget so the QSS stylesheet can style it uniformly
        self.setObjectName("MetricBlock")
        # Remember which metric this block represents for lookups
        self._metric = metric
        # Store whether we should render the AVG/MIN/MAX stats row
        self._show_stats = show_stats
        # Store whether we should render the animated progress bar
        self._show_bar = show_bar
        # Seed the smooth-animation state at the initial value (or zero if no bar)
        self._smooth = float(value) if show_bar else 0.0
        # Set the initial target so the first tick converges on the starting value
        self._target = float(value) if show_bar else 0.0
        # Create a vertical layout to stack label, value row, bar, and stats
        layout = QVBoxLayout(self)
        # Add horizontal gutters so text doesn't touch edges, minimal vertical padding
        layout.setContentsMargins(10, 2, 10, 2)
        # Zero spacing between rows for a dense, compact display
        layout.setSpacing(0)

        # Build the row containing the label on the left and value+unit on the right
        val_row = QHBoxLayout()
        # Create the descriptive label (e.g. "Distance")
        self._lbl = QLabel(label)
        # Assign the shared metric-label CSS class for consistent font/size
        self._lbl.setObjectName("MetricLabel")
        # Create the label that shows the current numeric value
        self._val = QLabel(str(value))
        # Assign the shared metric-value CSS class for large bold digits
        self._val.setObjectName("MetricValue")
        # Create the unit-of-measure label (e.g. "km", "g")
        self._unit = QLabel(unit)
        # Assign the shared metric-unit CSS class for smaller-dimension text
        self._unit.setObjectName("MetricUnit")
        # Attach label to the left side of the row
        val_row.addWidget(self._lbl)
        # Insert an elastic spacer to right-align value+unit
        val_row.addStretch()
        # Place the value after the spacer (right side)
        val_row.addWidget(self._val)
        # Place the unit immediately after the value
        val_row.addWidget(self._unit)
        # Attach the completed value row to the main vertical layout
        layout.addLayout(val_row)

        # Build the animated progress bar only when the caller requests it
        if show_bar:
            # Create a horizontal progress bar to give visual context to the metric
            self._bar = QProgressBar()
            # Use the same bar styling as temperature blocks for visual consistency
            self._bar.setObjectName("TempBar")
            # Internal range is 0-100 (we map the metric's range to a percentage)
            self._bar.setRange(0, 100)
            # Start at zero; animation will ramp it up smoothly
            self._bar.setValue(0)
            # Hide the default "42%" text for a clean bar-only look
            self._bar.setTextVisible(False)
            # Keep the bar thin so it doesn't dominate the block visually
            self._bar.setFixedHeight(8)
            # Store the lower bound for percentage calculation
            self._bar_min = 0.0
            # Store the upper bound so the caller can control the bar's full scale
            self._bar_max = float(bar_max)
            # Insert the bar below the value row
            layout.addWidget(self._bar)

            # Create a timer that fires at ~60 fps for smooth animation
            self._anim = QTimer(self)
            # Route each tick to the private smoothing method
            self._anim.timeout.connect(self._tick)
            # Kick off the animation loop immediately
            self._anim.start(16)

        # Create stat labels so they exist regardless of whether stats are shown
        self._avg = QLabel()
        self._min = QLabel()
        self._max = QLabel()
        # Build the AVG/MIN/MAX row only when the caller needs it
        if show_stats:
            # Create a horizontal row for the three stat boxes
            stats_row = QHBoxLayout()
            # Tight margins so the three boxes sit close together
            stats_row.setContentsMargins(2, 0, 2, 0)
            # Apply uniform CSS class and centered alignment to all stat labels
            for w in (self._avg, self._min, self._max):
                w.setObjectName("StatValue")
                w.setAlignment(Qt.AlignCenter)
                w.setText("-")
            # Add AVG, MIN, and MAX boxes in left-to-right order
            stats_row.addWidget(self._stat_box("AVG", self._avg))
            stats_row.addWidget(self._stat_box("MIN", self._min))
            stats_row.addWidget(self._stat_box("MAX", self._max))
            # Attach the stats row at the bottom of the layout
            layout.addLayout(stats_row)

        # Commit the layout to this widget
        self.setLayout(layout)

    # Run every animation frame to smoothly transition the displayed value toward its target
    def _tick(self):
        # Compute the remaining distance between current smooth value and the target
        diff = self._target - self._smooth
        # Snap to target when the difference is negligible to avoid perpetual micro-adjustments
        if abs(diff) < 0.005:
            self._smooth = self._target
        else:
            # Move 20% of the remaining distance per frame for a smooth exponential ease
            self._smooth += diff * 0.2
        # Render the smoothed value with two decimal places
        self._val.setText(f"{self._smooth:.2f}")
        # Convert the smoothed value into a 0-100 percentage relative to the bar range
        pct = (self._smooth - self._bar_min) / (self._bar_max - self._bar_min) * 100
        # Clamp the percentage to the valid range so the bar never overflows
        pct = max(0, min(100, pct))
        # Update the progress bar's visual position
        self._bar.setValue(int(pct))
        # Start with the default cyan accent color
        c = QColor("#00d4ff")
        # Switch to red for critical levels to grab the operator's attention
        if pct > 75:
            c = QColor(255, 80, 80)
        # Switch to amber/orange for warning levels
        elif pct > 50:
            c = QColor(255, 180, 50)
        # Apply the dynamic color to the progress bar chunk via a runtime stylesheet
        self._bar.setStyleSheet(
            f"QProgressBar::chunk {{ background: {c.name()}; border-radius: 4px; }}"
        )

    # Build a compact container with a stat label (e.g. "AVG") above a value label
    def _stat_box(self, lbl, val):
        # Outer container widget to hold the label-value pair
        w = QWidget()
        # Vertical layout stacks the stat name above its value
        l = QVBoxLayout(w)
        # Minimal margins to keep the stats row dense
        l.setContentsMargins(2, 0, 2, 0)
        # No spacing between the name and the value for a tight look
        l.setSpacing(0)
        # Add the capitalized stat name (e.g. "AVG") as the top label
        l.addWidget(QLabel(lbl, objectName="StatLabel", alignment=Qt.AlignCenter))
        # Add the dynamic value label below the stat name
        l.addWidget(val)
        # Return the assembled stat box
        return w

    # Receive a new value from the data pipeline and dispatch for display
    def update_value(self, v):
        # When the animated bar is active, set the target for smooth interpolation
        if self._show_bar:
            self._target = float(v)
        else:
            # Without a bar, update the text directly, accepting both string and numeric types
            self._val.setText(v) if isinstance(v, str) else self._val.setText(f"{v}")

    # Receive fresh AVG/MIN/MAX stats and push them into the stat labels
    def update_stats(self, avg, mn, mx):
        # Only touch the labels when the stats row is actually visible
        if self._show_stats:
            self._avg.setText(avg if avg is not None else "-")
            self._min.setText(mn if mn is not None else "-")
            self._max.setText(mx if mx is not None else "-")


class AccelGForceDistance(QWidget):
    """Panel displaying acceleration, G-force, distance, and estimated rounds."""

    # Set up the full panel with its four metric subsections
    def __init__(self, index=0, parent=None):
        # Initialize the underlying QWidget properly
        super().__init__(parent)
        # Store the index so a parent grid layout can identify this panel
        self._index = index
        # Main vertical layout holding the header and all metric blocks
        layout = QVBoxLayout(self)
        # Small uniform padding to keep content away from panel borders
        layout.setContentsMargins(4, 4, 4, 4)
        # Tight spacing so metrics are visually grouped but still distinct
        layout.setSpacing(4)

        # Panel title identifying the group of metrics
        header = QLabel("Acceleration · G‑Force · Distance")
        # Use the shared panel-title CSS class for consistent font across all panels
        header.setObjectName("PanelTitle")
        # Center the title horizontally
        header.setAlignment(Qt.AlignCenter)
        # Place the title at the very top
        layout.addWidget(header)

        # Create the acceleration metric with coral accent and 0-30 m/s² range
        self._accel = TempMetricBlock("accel", "Acceleration", min_val=0, max_val=30, unit="m/s²", accent_color="#ff7f50")

        # Factory that produces a thin horizontal separator line between sections
        def _sep():
            s = QFrame()
            s.setObjectName("ValueSeparator")
            return s

        # Add the acceleration block with stretch=1 so it gets equal vertical space
        layout.addWidget(self._accel, 1)
        # Insert a separator between acceleration and the G-force block
        layout.addWidget(_sep())

        # Create the G-force metric with green accent and 0-5 g range
        self._gforce = TempMetricBlock("gforce", "G‑Force", min_val=0, max_val=5, unit="g", accent_color="#00ffa6")
        # Create a static distance block (no bar, no stats — just a number and unit)
        self._distance = _PlainBlock("distance", "Distance", "0.0", "km", show_stats=False)
        # Create a static rounds counter with no unit label (just an integer)
        self._rounds = _PlainBlock("rounds", "Est. Rounds", "0", "", show_stats=False)

        # Add the G-force block as the third section
        layout.addWidget(self._gforce, 1)
        # Separate G-force from the distance section
        layout.addWidget(_sep())
        # Add the distance display
        layout.addWidget(self._distance, 1)
        # Separate distance from the rounds section
        layout.addWidget(_sep())
        # Add the estimated-rounds counter as the final section
        layout.addWidget(self._rounds, 1)
        # Finalize the layout assignment
        self.setLayout(layout)

    # Called every tick to push fresh telemetry data into all child metric blocks
    def update_from_data(self, d):
        """Update acceleration, G-force, distance, and rounds from a DisplayData object."""
        # Push the latest acceleration reading into the animated block
        self._accel.update_value(d.acceleration)
        # Update the acceleration AVG/MIN/MAX stats with two-decimal formatting
        self._accel.update_stats(f"{d.acceleration_avg:.2f}", f"{d.acceleration_min:.2f}", f"{d.acceleration_max:.2f}")
        # Push the latest G-force value into its animated block
        self._gforce.update_value(d.g_force)
        # Update the G-force AVG/MIN/MAX stats
        self._gforce.update_stats(f"{d.gforce_avg:.2f}", f"{d.gforce_min:.2f}", f"{d.gforce_max:.2f}")
        # Update the distance display with one decimal place
        self._distance.update_value(f"{d.distance:.1f}")
        # Update the estimated-rounds count (integer, no decimals)
        self._rounds.update_value(f"{d.estimated_rounds:.0f}")

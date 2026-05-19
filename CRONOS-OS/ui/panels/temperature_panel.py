"""Temperature display widgets with animated progress bars and stats.

Widgets:
    CombinedTempPanel: Panel showing battery, chip, and engine temperature blocks.
    TempMetricBlock: Single temperature metric with animated bar and AVG/MIN/MAX stats.
    TempBlock: Core animated progress-bar widget used internally by TempMetricBlock.
"""

# Import all Qt widget classes needed for the temperature display panel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
# Import Qt enums and timer for alignment constants and animation loops
from PySide6.QtCore import Qt, QTimer
# Import QColor for dynamic bar color transitions based on temperature severity
from PySide6.QtGui import QColor


class TempBlock(QWidget):
    """Animated progress-bar block for a single temperature metric with smoothing."""

    # Build an animated temperature block with a label, value row, and progress bar
    def __init__(self, metric, label, value, unit, min_val=0, max_val=100, accent_color="#00aaff", parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Tag this widget so the QSS stylesheet can target it
        self.setObjectName("TempBlock")
        # Store the metric key for data-binding identification
        self._metric = metric
        # Remember the temperature range minimum (used for percentage mapping)
        self._min_val = min_val
        # Remember the temperature range maximum (used for percentage mapping)
        self._max_val = max_val
        # Seed the smooth animator's current value at zero
        self._smooth = 0.0
        # Set the initial target value (animator converges toward this)
        self._target = 0.0
        # Seed the bar-position smoother at zero
        self._bar_pct = 0.0

        # Main vertical layout for the block
        layout = QVBoxLayout(self)
        # Horizontal padding with moderate vertical padding
        layout.setContentsMargins(10, 4, 10, 4)
        # Tight spacing between stacked rows
        layout.setSpacing(2)

        # Create the metric label (e.g. "Battery")
        lbl = QLabel(label)
        # Shared metric-label styling
        lbl.setObjectName("MetricLabel")
        # Add the label at the top
        layout.addWidget(lbl)

        # Horizontal row for the numeric value and unit
        val_row = QHBoxLayout()
        # Label showing the current temperature reading
        self._value = QLabel(str(value))
        # Large-value font styling
        self._value.setObjectName("MetricValue")
        # Unit label (e.g. "°C")
        self._unit = QLabel(unit)
        # Smaller-dimension styling for the unit
        self._unit.setObjectName("MetricUnit")
        # Left spacer to center the value+unit
        val_row.addStretch()
        # Add the numeric value
        val_row.addWidget(self._value)
        # Add the unit immediately after
        val_row.addWidget(self._unit)
        # Right spacer to complete centering
        val_row.addStretch()
        # Attach the value row below the label
        layout.addLayout(val_row)

        # Animated progress bar showing the temperature visually
        self._bar = QProgressBar()
        # Shared temperature-bar styling
        self._bar.setObjectName("TempBar")
        # Internal range is 0-100% (mapped from min_val-max_val)
        self._bar.setRange(0, 100)
        # Start at zero; animator fills it in
        self._bar.setValue(0)
        # Hide default percentage text
        self._bar.setTextVisible(False)
        # Thin bar to keep the block compact
        self._bar.setFixedHeight(8)
        # Add the bar below the value row
        layout.addWidget(self._bar)

        # 60fps animation timer for smooth value and bar transitions
        self._anim = QTimer(self)
        # Connect ticks to the smoothing method
        self._anim.timeout.connect(self._tick)
        # Start the animation loop immediately
        self._anim.start(16)

        # Finalize the layout
        self.setLayout(layout)

    # Animation tick: smooth both the value text and the bar position with color transitions
    def _tick(self):
        # Calculate remaining distance to the target value
        diff = self._target - self._smooth
        # Snap to target when close to avoid jitter
        if abs(diff) < 0.05:
            self._smooth = self._target
        else:
            # Move 20% of the gap per frame for exponential easing
            self._smooth += diff * 0.2
        # Update the value label with one decimal place
        self._value.setText(f"{self._smooth:.1f}")

        # Convert the smooth value to a 0-100 percentage based on the configured range
        try:
            pct = (self._smooth - self._min_val) / (self._max_val - self._min_val) * 100
            # Clamp to valid 0-100 range
            pct = max(0, min(100, pct))
            # Calculate the bar-position gap for independent smoothing
            bar_diff = pct - self._bar_pct
            # Snap the bar when close to the target
            if abs(bar_diff) < 0.1:
                self._bar_pct = pct
            else:
                # Move the bar 20% of the remaining gap per frame
                self._bar_pct += bar_diff * 0.2
            # Update the bar's visual position
            self._bar.setValue(int(self._bar_pct))
            # Default bar color is blue (cold/normal)
            c = QColor(0, 170, 255)
            # Switch to red for critical temperature (>75%)
            if self._bar_pct > 75:
                c = QColor(255, 80, 80)
            # Switch to amber for warning temperature (50-75%)
            elif self._bar_pct > 50:
                c = QColor(255, 180, 50)
            # Apply the dynamic color via inline stylesheet
            self._bar.setStyleSheet(
                f"QProgressBar::chunk {{ background: {c.name()}; border-radius: 4px; }}"
            )
        # Silently ignore any math errors (e.g. division by zero from equal min/max)
        except Exception:
            pass

    # Set a new target value; the animation loop will smoothly converge on it
    def update_value(self, value):
        """Set the target value; animator smoothly converges on it."""
        self._target = float(value)


# Factory that creates a reusable stats-row layout with AVG/MIN/MAX labels
def _stats_row():
    # Horizontal layout for the three stat boxes
    row = QHBoxLayout()
    # Tight margins between boxes
    row.setContentsMargins(2, 0, 2, 0)
    # Create the three stat value labels with default placeholders and shared styling
    avg = QLabel("-", objectName="StatValue", alignment=Qt.AlignCenter)
    mn = QLabel("-", objectName="StatValue", alignment=Qt.AlignCenter)
    mx = QLabel("-", objectName="StatValue", alignment=Qt.AlignCenter)

    # Inner factory that builds a labeled stat box (e.g. "AVG" above a value)
    def box(lbl, val):
        # Container for the label-value pair
        w = QWidget()
        # Vertical layout stacks the label above the value
        l = QVBoxLayout(w)
        # Tight margins
        l.setContentsMargins(2, 0, 2, 0)
        # No gap between the name and the value
        l.setSpacing(0)
        # Add the capitalized stat name centered
        l.addWidget(QLabel(lbl, objectName="StatLabel", alignment=Qt.AlignCenter))
        # Add the numeric value below
        l.addWidget(val)
        # Return the assembled box
        return w
    # Add the three stat boxes to the horizontal row
    row.addWidget(box("AVG", avg))
    row.addWidget(box("MIN", mn))
    row.addWidget(box("MAX", mx))
    # Return the row layout and all three value labels so callers can update them later
    return row, avg, mn, mx


class TempMetricBlock(QWidget):
    """Temperature metric with animated bar and AVG / MIN / MAX stats row."""

    # Compose a TempBlock with an attached AVG/MIN/MAX stats row below it
    def __init__(self, metric, label, min_val=0, max_val=100, unit="°C", accent_color="#00aaff", parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Store the metric key for identification
        self._metric = metric
        # Create the core animated TempBlock (label + value + progress bar)
        self._block = TempBlock(metric, label, 0, unit, min_val=min_val, max_val=max_val, accent_color=accent_color)
        # Main vertical layout
        layout = QVBoxLayout(self)
        # Zero margins so this composite block fits seamlessly into parent panels
        layout.setContentsMargins(0, 0, 0, 0)
        # No spacing between the TempBlock and the stats row
        layout.setSpacing(0)
        # Add the TempBlock at the top
        layout.addWidget(self._block)
        # Create the stats row via the factory; unpack the layout and labels
        sr, self._avg, self._min, self._max = _stats_row()
        # Keep references to the stat labels for later updates
        self._avg_lbl = self._avg
        self._min_lbl = self._min
        self._max_lbl = self._max
        # Attach the stats row below the TempBlock
        layout.addLayout(sr)
        # Finalize the layout
        self.setLayout(layout)

    # Forward a new temperature value to the animated TempBlock
    def update_value(self, v):
        """Forward a new value to the animated TempBlock."""
        self._block.update_value(v)

    # Push fresh AVG/MIN/MAX values into the stat labels, falling back to "-" for None
    def update_stats(self, avg, mn, mx):
        self._avg.setText(avg if avg is not None else "-")
        self._min.setText(mn if mn is not None else "-")
        self._max.setText(mx if mx is not None else "-")


class CombinedTempPanel(QWidget):
    """Panel displaying battery, chip, and engine temperatures with per-metric stats."""

    # Compose the full temperature panel with battery, chip, and engine blocks
    def __init__(self, index=0, parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Store the grid index for identification
        self._index = index
        # Main vertical layout for the panel
        layout = QVBoxLayout(self)
        # Micro-padding around panel edges
        layout.setContentsMargins(4, 4, 4, 4)
        # Tight spacing between the three temperature sections
        layout.setSpacing(2)

        # Panel header identifying this section
        header = QLabel("Temperatures")
        # Shared panel-title styling
        header.setObjectName("PanelTitle")
        # Center the header
        header.setAlignment(Qt.AlignCenter)
        # Add the header at the top
        layout.addWidget(header)

        # Create the three temperature metric blocks
        self._battery = TempMetricBlock("battery", "Battery")
        self._chip = TempMetricBlock("chip", "Chip")
        self._engine = TempMetricBlock("engine", "Engine")

        # Factory that produces a thin horizontal separator frame
        def _sep():
            s = QFrame()
            s.setObjectName("ValueSeparator")
            return s

        # Add battery block with stretch=1 for equal height distribution
        layout.addWidget(self._battery, 1)
        # Separate battery from chip
        layout.addWidget(_sep())
        # Add chip block with stretch=1
        layout.addWidget(self._chip, 1)
        # Separate chip from engine
        layout.addWidget(_sep())
        # Add engine block with stretch=1
        layout.addWidget(self._engine, 1)
        # Vertically center all panel contents
        layout.setAlignment(Qt.AlignVCenter)
        # Finalize the layout
        self.setLayout(layout)

    # Called every tick to refresh all temperature displays from fresh telemetry data
    def update_from_data(self, d):
        """Update all temperature blocks and stats from a DisplayData object."""
        # Update battery temperature value
        self._battery.update_value(d.temperature_battery)
        # Update battery AVG/MIN/MAX stats with one-decimal formatting
        self._battery.update_stats(f"{d.temp_battery_avg:.1f}", f"{d.temp_battery_min:.1f}", f"{d.temp_battery_max:.1f}")
        # Update chip temperature value
        self._chip.update_value(d.temperature_chip)
        # Update chip AVG/MIN/MAX stats
        self._chip.update_stats(f"{d.temp_chip_avg:.1f}", f"{d.temp_chip_min:.1f}", f"{d.temp_chip_max:.1f}")
        # Update engine temperature value
        self._engine.update_value(d.temperature_engine)
        # Update engine AVG/MIN/MAX stats
        self._engine.update_stats(f"{d.temp_engine_avg:.1f}", f"{d.temp_engine_min:.1f}", f"{d.temp_engine_max:.1f}")


def combinedTempPanel(index):
    return CombinedTempPanel(index)

"""Electrical values display (voltage, current, power, energy, battery %).

Widgets:
    CombinedPowerPanel: Panel showing device/battery voltage, battery %, current, power, energy.
    PowerMetricBlock: Single electrical metric with optional animated bar and AVG/MIN/MAX stats.
"""

# Import all Qt widget classes needed for the electrical display panel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
# Import Qt enums and timer for alignment constants and animation
from PySide6.QtCore import Qt, QTimer
# Import QColor for dynamic color transitions on the animated bar
from PySide6.QtGui import QColor


class _MetricBlock(QWidget):
    """Static metric display block (label + value + unit, no animation)."""

    # Build a read-only metric row showing a label, a numeric value, and a unit
    def __init__(self, metric, label, value, unit, accent_color="#00d4ff", parent=None):
        # Initialize the Qt widget properly
        super().__init__(parent)
        # Tag this widget so the QSS stylesheet can target it
        self.setObjectName("MetricBlock")
        # Store the metric key for data-binding or logging purposes
        self._metric = metric
        # Retain the accent color for potential future styling use
        self._accent = accent_color

        # Main vertical layout for the static block
        layout = QVBoxLayout(self)
        # Moderate horizontal padding, minimal vertical padding
        layout.setContentsMargins(8, 2, 8, 2)
        # No spacing between the label and value rows
        layout.setSpacing(0)

        # Create the metric label (e.g. "Voltage Device")
        self._label = QLabel(label)
        # Apply shared metric-label CSS class
        self._label.setObjectName("MetricLabel")
        # Attach the label at the top of the block
        layout.addWidget(self._label)

        # Horizontal row for the value and unit
        val_row = QHBoxLayout()
        # Label that displays the current numeric value
        self._value = QLabel(str(value))
        # Large-value CSS class for prominent digits
        self._value.setObjectName("MetricValue")
        # Label showing the unit of measure (e.g. "V", "A", "W")
        self._unit = QLabel(unit)
        # Smaller-dimension CSS class for the unit
        self._unit.setObjectName("MetricUnit")
        # Left elastic spacer to center the value+unit
        val_row.addStretch()
        # Add the numeric value
        val_row.addWidget(self._value)
        # Add the unit immediately after
        val_row.addWidget(self._unit)
        # Right elastic spacer to complete centering
        val_row.addStretch()
        # Attach the value row below the label
        layout.addLayout(val_row)

        # Commit the layout
        self.setLayout(layout)

    # Update the displayed value text
    def update_value(self, value):
        self._value.setText(str(value))


class _StatsRow(QWidget):
    """AVG / MIN / MAX statistics row for a metric."""

    # Build a horizontal row with three labeled stat boxes
    def __init__(self, metric, parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Store the associated metric key
        self._metric = metric
        # Horizontal layout arranges AVG, MIN, MAX side by side
        layout = QHBoxLayout(self)
        # Tight margins between the stat boxes
        layout.setContentsMargins(2, 0, 2, 0)
        # Create the three stat value labels with default placeholder text
        self._avg = QLabel("-")
        self._min = QLabel("-")
        self._max = QLabel("-")
        # Apply uniform styling and centered alignment to all three labels
        for w in (self._avg, self._min, self._max):
            w.setObjectName("StatValue")
            w.setAlignment(Qt.AlignCenter)
        # Add labeled stat boxes in left-to-right order
        layout.addWidget(self._stat_box("AVG", self._avg))
        layout.addWidget(self._stat_box("MIN", self._min))
        layout.addWidget(self._stat_box("MAX", self._max))
        # Commit the layout
        self.setLayout(layout)

    # Build a compact container with a stat label above a value label
    def _stat_box(self, lbl, val):
        # Container widget for the pair
        w = QWidget()
        # Vertical layout stacks the label above the value
        l = QVBoxLayout(w)
        # Minimal margins
        l.setContentsMargins(2, 0, 2, 0)
        # No gap between the stat name and its value
        l.setSpacing(0)
        # Add the capitalized stat name (e.g. "AVG") centered
        l.addWidget(QLabel(lbl, objectName="StatLabel", alignment=Qt.AlignCenter))
        # Add the numeric value label below
        l.addWidget(val)
        # Return the assembled box
        return w

    # Push fresh values into the three stat labels, falling back to "-" for None
    def update_stats(self, avg, mn, mx):
        self._avg.setText(avg if avg is not None else "-")
        self._min.setText(mn if mn is not None else "-")
        self._max.setText(mx if mx is not None else "-")


class PowerMetricBlock(QWidget):
    """Single electrical metric with optional animated bar and AVG/MIN/MAX stats."""

    # Build a metric block with a static _MetricBlock, optional animated bar, and optional stats
    def __init__(self, index, metric, label, value, unit, accent_color="#00d4ff", show_bar=False, bar_max=100, show_stats=True, parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Main vertical layout
        layout = QVBoxLayout(self)
        # Zero margins for seamless integration into parent containers
        layout.setContentsMargins(0, 0, 0, 0)
        # Moderate spacing between the block, bar, and stats row
        layout.setSpacing(8)
        # Create the static label+value+unit block
        self._block = _MetricBlock(metric, label, value, unit, accent_color)
        # Add the static block at the top
        layout.addWidget(self._block)
        # Conditionally build the animated progress bar
        if show_bar:
            # Create a horizontal progress bar for visual context
            self._bar = QProgressBar()
            # Use the temperature-bar styling for consistency
            self._bar.setObjectName("TempBar")
            # Internal 0-100 percentage range
            self._bar.setRange(0, 100)
            # Start at zero; the animator fills it in
            self._bar.setValue(0)
            # Hide default percentage text
            self._bar.setTextVisible(False)
            # Thin bar to keep the block compact
            self._bar.setFixedHeight(8)
            # Insert the bar below the metric block
            layout.addWidget(self._bar)
            # Store the upper bound for percentage-to-bar mapping
            self._bar_max = float(bar_max)
            # Seed the smooth value at the initial value
            self._smooth = float(value)
            # Set the target to the same initial value
            self._target = float(value)
            # Create a 60fps animation timer for smooth transitions
            self._anim = QTimer(self)
            # Connect ticks to the smoothing method
            self._anim.timeout.connect(self._tick)
            # Start the animation loop
            self._anim.start(16)
        else:
            # No bar present; mark it as None for null-safe checks
            self._bar = None
        # Create the stats row only when the caller requests it
        self._stats = _StatsRow(metric) if show_stats else None
        # Attach the stats row if it was created
        if self._stats:
            layout.addWidget(self._stats)
        # Commit the layout
        self.setLayout(layout)

    # Animation tick: smooth the displayed value and the progress bar position
    def _tick(self):
        # Calculate remaining distance to the target value
        diff = self._target - self._smooth
        # Snap to target when close to avoid jitter
        if abs(diff) < 0.05:
            self._smooth = self._target
        else:
            # Move 20% of the gap per frame for exponential easing
            self._smooth += diff * 0.2
        # Update the inner static block's value label with the smoothed integer
        self._block._value.setText(f"{self._smooth:.0f}")
        # Convert the smooth value to a percentage of the bar's max range
        pct = self._smooth / self._bar_max * 100
        # Clamp to valid 0-100 range
        pct = max(0, min(100, pct))
        # Update the bar position
        self._bar.setValue(int(pct))
        # Default bar color is green (nominal range)
        c = QColor("#2ecc71")
        # Switch to red when the value is low (<30%) to draw attention
        if pct < 30:
            c = QColor("#ff5050")
        # Switch to amber/yellow for moderate-low values (30-50%)
        elif pct < 50:
            c = QColor("#ffb432")
        # Apply the dynamic color via an inline stylesheet
        self._bar.setStyleSheet(
            f"QProgressBar::chunk {{ background: {c.name()}; border-radius: 4px; }}"
        )

    # Receive a new value; route it to the animator or display it directly
    def update_value(self, v):
        """Update the displayed value; uses smooth animation when bar is active."""
        # When an animated bar exists, set the target for the smoother
        if self._bar is not None:
            self._target = float(v)
        else:
            # Without animation, update the static block immediately
            self._block.update_value(v)

    # Receive fresh AVG/MIN/MAX stats and forward them to the stats row
    def update_stats(self, avg, mn, mx):
        if self._stats:
            self._stats.update_stats(avg, mn, mx)


class CombinedPowerPanel(QWidget):
    """Panel displaying device/battery voltage, battery %, current, power, and energy."""

    # Compose the full electrical panel with all six metric blocks
    def __init__(self, index=0, parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Store the grid index for identification by parent layouts
        self._index = index

        # Main vertical layout for the panel
        layout = QVBoxLayout(self)
        # Micro-padding around the panel edges
        layout.setContentsMargins(4, 4, 4, 4)
        # Tight spacing between sections
        layout.setSpacing(3)

        # Panel title identifying this section
        header = QLabel("Electrical")
        # Shared panel-title styling
        header.setObjectName("PanelTitle")
        # Center the header
        header.setAlignment(Qt.AlignCenter)
        # Add the header at the top
        layout.addWidget(header)

        # Create all six metric blocks (voltage x2, battery, current, power, energy)
        self._voltage = PowerMetricBlock(index, "voltage", "Voltage Device", 0, "V")
        self._voltage2 = PowerMetricBlock(index, "voltage_battery", "Voltage Battery", 0, "V")
        self._battery = PowerMetricBlock(index, "battery", "Battery", 0, "%", show_bar=True, show_stats=False)
        self._current = PowerMetricBlock(index, "current", "Current", 0, "A")
        self._power = PowerMetricBlock(index, "power", "Power", 0, "W")
        self._energy = PowerMetricBlock(index, "energy", "Energy", 0, "kWh", show_stats=False)

        # Horizontal row putting both voltage metrics side by side
        voltage_row = QHBoxLayout()
        # Zero margins so the row blends into the parent layout
        voltage_row.setContentsMargins(0, 0, 0, 0)
        # Spacing between the two voltage blocks
        voltage_row.setSpacing(8)
        # Add device voltage with equal stretch
        voltage_row.addWidget(self._voltage, 1)
        # Add battery voltage with equal stretch
        voltage_row.addWidget(self._voltage2, 1)

        # Horizontal row putting current and power side by side
        power_row = QHBoxLayout()
        # Zero margins
        power_row.setContentsMargins(0, 0, 0, 0)
        # Spacing between the two blocks
        power_row.setSpacing(8)
        # Add current with equal stretch
        power_row.addWidget(self._current, 1)
        # Add power with equal stretch
        power_row.addWidget(self._power, 1)

        # Factory that creates a thin horizontal separator frame
        def _sep():
            s = QFrame()
            s.setObjectName("ValueSeparator")
            return s

        # Add the voltage row as the first major section (stretch=1)
        layout.addLayout(voltage_row, 1)
        # Separate voltage from battery
        layout.addWidget(_sep())
        # Add the battery block (no stretch — fixed height)
        layout.addWidget(self._battery)
        # Separate battery from power
        layout.addWidget(_sep())
        # Add the current+power row as the next section (stretch=1)
        layout.addLayout(power_row, 1)
        # Separate power from energy
        layout.addWidget(_sep())
        # Add the energy block at the bottom
        layout.addWidget(self._energy)
        # Vertically center all panel contents
        layout.setAlignment(Qt.AlignVCenter)
        # Finalize the layout
        self.setLayout(layout)

    # Called every tick to refresh all electrical metrics from fresh telemetry data
    def update_from_data(self, d):
        """Update all electrical metrics and stats from a DisplayData object."""
        # Update device voltage with two-decimal formatting
        self._voltage.update_value(f"{d.voltage:.2f}")
        # Update device voltage AVG/MIN/MAX stats
        self._voltage.update_stats(f"{d.voltage_avg:.2f}", f"{d.voltage_min:.2f}", f"{d.voltage_max:.2f}")
        # Update battery voltage with two-decimal formatting
        self._voltage2.update_value(f"{d.voltage_battery:.2f}")
        # Update battery voltage AVG/MIN/MAX stats (uses same voltage stats from telemetry)
        self._voltage2.update_stats(f"{d.voltage_avg:.2f}", f"{d.voltage_min:.2f}", f"{d.voltage_max:.2f}")
        # Update battery percentage (drives the animated bar)
        self._battery.update_value(d.battery_pct)
        # Update current with two-decimal formatting
        self._current.update_value(f"{d.current:.2f}")
        # Update current AVG/MIN/MAX stats
        self._current.update_stats(f"{d.current_avg:.2f}", f"{d.current_min:.2f}", f"{d.current_max:.2f}")
        # Update power with one-decimal formatting
        self._power.update_value(f"{d.power:.1f}")
        # Update power AVG/MIN/MAX stats
        self._power.update_stats(f"{d.power_avg:.1f}", f"{d.power_min:.1f}", f"{d.power_max:.1f}")
        # Update energy with three-decimal formatting (kWh often has small increments)
        self._energy.update_value(f"{d.energy_kwh:.3f}")


def combinedPowerPanel(index, voltage, voltage_unit, voltage_stats, current, current_unit, current_stats, power, power_unit, power_stats, title, accent_color):
    w = CombinedPowerPanel(index)
    return w

"""Settings panel with alarm limits, target time, serial port info, and feature toggles.

Widgets:
    SettingsPanel: Sidebar panel exposing user-configurable parameters.
    _AlarmRow: Single alarm-limit row (label + QLineEdit + unit).
"""

# Import all Qt widgets needed for the settings form layout
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QTimeEdit, QComboBox
# Import Qt enums and QTime for time-picker configuration
from PySide6.QtCore import Qt, QTime
# Import the custom toggle switch used for boolean feature toggles
from ui.components.check_button import ToggleSwitch


class _AlarmRow(QWidget):
    """Single alarm-limit row: label, integer QLineEdit, and unit label."""

    # Build a horizontal row with a label, a text input, and a unit label for one alarm threshold
    def __init__(self, metric, label, unit="°C", parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Store the metric key so the caller can identify which alarm this row represents
        self._metric = metric
        # Horizontal layout arranges the label, input, and unit side by side
        layout = QHBoxLayout(self)
        # Small horizontal margins, minimal vertical padding
        layout.setContentsMargins(4, 2, 4, 2)

        # Create the descriptive label (e.g. "Engine")
        lbl = QLabel(label)
        # Apply the settings-label CSS class for consistent form styling
        lbl.setObjectName("SettingsLabel")
        # Create the text input for the threshold value; default to 100 for °C, 20 for other units
        self._input = QLineEdit("100" if unit == "°C" else "20")
        # Apply the settings-input CSS class for consistent field styling
        self._input.setObjectName("SettingsInput")
        # Limit to 3 characters (typical alarm thresholds are 0-999)
        self._input.setMaxLength(3)
        # Fixed width to keep the row compact across different alarm rows
        self._input.setFixedWidth(50)
        # Center the typed value inside the input field
        self._input.setAlignment(Qt.AlignCenter)
        # Create the unit label (e.g. "°C", "%")
        unit_lbl = QLabel(unit)
        # Apply the same settings-label styling for the unit
        unit_lbl.setObjectName("SettingsLabel")

        # Add elements left to right: label | input | unit
        layout.addWidget(lbl)
        layout.addWidget(self._input)
        layout.addWidget(unit_lbl)
        # Push everything to the left with a trailing stretch
        layout.addStretch()
        # Finalize the layout
        self.setLayout(layout)

    # Read and return the integer value from the text input, or None if parsing fails
    def value(self):
        try:
            return int(self._input.text())
        except ValueError:
            return None

    # Programmatically set the input field to a given integer value
    def set_value(self, v):
        self._input.setText(str(v))


class SettingsPanel(QWidget):
    """Sidebar panel for user-configurable settings including alarms, time, toggles, and serial/CSV info."""

    # Build the full settings panel with all configuration sections
    def __init__(self, index=0, parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Store the grid index for identification
        self._index = index

        # Assign a CSS class so the stylesheet can give this panel a distinct background
        self.setObjectName("SettingsPanel")
        # Main vertical layout for the entire settings form
        layout = QVBoxLayout(self)
        # Moderate padding around the panel edges for readability
        layout.setContentsMargins(8, 8, 8, 8)
        # Moderate spacing between form sections
        layout.setSpacing(6)

        # Panel header identifying this section
        header = QLabel("Settings")
        # Shared panel-title styling
        header.setObjectName("PanelTitle")
        # Center the header
        header.setAlignment(Qt.AlignCenter)
        # Add the header at the top
        layout.addWidget(header)

        # Thin horizontal separator to visually divide the header from the content
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setObjectName("Separator")
        layout.addWidget(sep)

        # Section label for the target-time feature
        start_lbl = QLabel("Target Time")
        # Settings-label styling
        start_lbl.setObjectName("SettingsLabel")
        layout.addWidget(start_lbl)

        # Horizontal row containing the time editor and the "Now" button
        time_row = QHBoxLayout()
        # QTimeEdit widget for picking a target time
        self._time_edit = QTimeEdit()
        # Apply settings-input styling for consistency with other inputs
        self._time_edit.setObjectName("SettingsInput")
        # Display the time in 24-hour HH:MM:SS format
        self._time_edit.setDisplayFormat("HH:mm:ss")
        # Default to 08:00:00 as a sensible starting target
        self._time_edit.setTime(QTime(8, 0, 0))
        # Flag indicating whether the user has manually set the time (vs. the default)
        self._time_set = False
        # Mark the time as set whenever the user changes the QTimeEdit value
        self._time_edit.timeChanged.connect(self._on_time_changed)
        # Add the time editor to the row
        time_row.addWidget(self._time_edit)

        # "Now" button that sets the target time to the current wall-clock time
        self._start_btn = QPushButton("Now")
        # Apply the settings-button styling
        self._start_btn.setObjectName("SettingsButton")
        # Fixed narrow width to sit beside the time editor
        self._start_btn.setFixedWidth(50)
        # Connect the button click to the _set_current_time handler
        self._start_btn.clicked.connect(self._set_current_time)
        # Add the button to the row
        time_row.addWidget(self._start_btn)
        # Attach the time-picker row to the layout
        layout.addLayout(time_row)

        # Display label showing the formatted start time (initially matches the default)
        self._start_display = QLabel("08:00:00")
        # Distinct CSS class for the large start-time display
        self._start_display.setObjectName("StartDisplay")
        # Center the time display
        self._start_display.setAlignment(Qt.AlignCenter)
        # Add the display below the time row
        layout.addWidget(self._start_display)

        # Separator between the target-time section and the alarm limits section
        sep2 = QWidget()
        sep2.setFixedHeight(1)
        sep2.setObjectName("Separator")
        layout.addWidget(sep2)

        # Section label for alarm thresholds
        alarm_lbl = QLabel("Alarm Limits")
        # Settings-label styling
        alarm_lbl.setObjectName("SettingsLabel")
        layout.addWidget(alarm_lbl)

        # Create four alarm-limit rows for engine temperature, battery temp, chip temp, and battery %
        self._alarm_engine = _AlarmRow("engine", "Engine")
        self._alarm_battery_temp = _AlarmRow("battery_temp", "Battery Temp")
        self._alarm_chip = _AlarmRow("chip", "Chip")
        self._alarm_battery_pct = _AlarmRow("battery_pct", "Battery %", unit="%")
        # Add all four alarm rows to the layout
        layout.addWidget(self._alarm_engine)
        layout.addWidget(self._alarm_battery_temp)
        layout.addWidget(self._alarm_chip)
        layout.addWidget(self._alarm_battery_pct)

        # Horizontal row for the alarm-enable checkbox
        toggle_row = QHBoxLayout()
        # Checkbox that globally enables or disables all alarms
        self._alarm_toggle = QCheckBox()
        # Alarms are enabled by default for safety
        self._alarm_toggle.setChecked(True)
        # Label next to the checkbox
        toggle_lbl = QLabel("Enable Alarms")
        # Settings-label styling
        toggle_lbl.setObjectName("SettingsLabel")
        # Add checkbox and label to the row
        toggle_row.addWidget(self._alarm_toggle)
        toggle_row.addWidget(toggle_lbl)
        # Right-align by adding a trailing stretch
        toggle_row.addStretch()
        # Attach the toggle row
        layout.addLayout(toggle_row)

        # Separator between alarm section and feature toggles
        sep3 = QWidget()
        sep3.setFixedHeight(1)
        sep3.setObjectName("Separator")
        layout.addWidget(sep3)

        # Add toggle-switch rows for optional system features
        layout.addWidget(ToggleSwitch("System Sound", True))
        layout.addWidget(ToggleSwitch("Alerts", False))
        self._warn_toggle = ToggleSwitch("Log Warnings", True)
        layout.addWidget(self._warn_toggle)
        self._debug_toggle = ToggleSwitch("Debug Values", False)
        layout.addWidget(self._debug_toggle)

        # Separator between feature toggles and numeric settings
        sep4 = QWidget()
        sep4.setFixedHeight(1)
        sep4.setObjectName("Separator")
        layout.addWidget(sep4)

        # Round-length input: how many kilometers constitute one "round" (lap)
        round_lbl = QLabel("Round Length (km)")
        # Settings-label styling
        round_lbl.setObjectName("SettingsLabel")
        layout.addWidget(round_lbl)
        # Text input defaulting to 1.0 km
        self._round_input = QLineEdit("1.0")
        # Settings-input styling
        self._round_input.setObjectName("SettingsInput")
        # Center the typed value
        self._round_input.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._round_input)

        # Wheel circumference input: meters per revolution (used for speed/distance calcs)
        wheel_lbl = QLabel("Wheel Circumference (m)")
        # Settings-label styling
        wheel_lbl.setObjectName("SettingsLabel")
        layout.addWidget(wheel_lbl)
        # Text input defaulting to 2.0 meters
        self._wheel_input = QLineEdit("2.0")
        # Settings-input styling
        self._wheel_input.setObjectName("SettingsInput")
        # Center the typed value
        self._wheel_input.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._wheel_input)

        # Connection timeout input: how many milliseconds before considering serial as lost
        timeout_lbl = QLabel("Connection Timeout (ms)")
        # Settings-label styling
        timeout_lbl.setObjectName("SettingsLabel")
        layout.addWidget(timeout_lbl)
        # Text input defaulting to 3000 ms
        self._timeout_input = QLineEdit("3000")
        # Settings-input styling
        self._timeout_input.setObjectName("SettingsInput")
        # Center the typed value
        self._timeout_input.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._timeout_input)

        # Separator between numeric settings and serial-port info
        sep5 = QWidget()
        sep5.setFixedHeight(1)
        sep5.setObjectName("Separator")
        layout.addWidget(sep5)

        # Serial port label showing the currently active serial device path
        port_lbl = QLabel("Serial Port")
        # Settings-label styling
        port_lbl.setObjectName("SettingsLabel")
        layout.addWidget(port_lbl)
        # Display the actual port name (or "none" when no port is connected)
        self._port_label = QLabel("none")
        # Use the CSV-label styling (small mono-style text)
        self._port_label.setObjectName("CsvLabel")
        # Center the port name
        self._port_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._port_label)

        # Port selection row: refresh button + port combo + connect button
        port_row = QHBoxLayout()
        port_row.setContentsMargins(4, 2, 4, 2)
        self._port_refresh = QPushButton("Scan")
        self._port_refresh.setObjectName("SettingsButton")
        self._port_refresh.setFixedWidth(50)
        self._port_refresh.clicked.connect(self._refresh_ports)
        port_row.addWidget(self._port_refresh)
        self._port_combo = QComboBox()
        self._port_combo.setObjectName("SettingsInput")
        self._port_combo.setMinimumWidth(120)
        self._port_combo.addItem("(scan first)")
        port_row.addWidget(self._port_combo)
        self._port_connect = QPushButton("Connect")
        self._port_connect.setObjectName("SettingsButton")
        self._port_connect.setFixedWidth(70)
        self._port_connect.clicked.connect(self._on_connect_clicked)
        port_row.addWidget(self._port_connect)
        layout.addLayout(port_row)

        # Separator between serial port info and CSV logging info
        sep6 = QWidget()
        sep6.setFixedHeight(1)
        sep6.setObjectName("Separator")
        layout.addWidget(sep6)

        # CSV log filename display
        csv_lbl = QLabel("CSV Log")
        # Settings-label styling
        csv_lbl.setObjectName("SettingsLabel")
        layout.addWidget(csv_lbl)
        # Label showing the current CSV output filename
        self._csv_label = QLabel("telemetry_log.csv")
        # Same styling as the port label for visual consistency
        self._csv_label.setObjectName("CsvLabel")
        # Center the filename
        self._csv_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._csv_label)

        # Finalize the layout
        self.setLayout(layout)

    # Read and return the round-length value from the text input (parsed as float)
    def get_round_length(self) -> float:
        """Return the round-length value from the text input (default 1.0 km)."""
        try:
            return float(self._round_input.text())
        except ValueError:
            return 1.0

    # Read and return the wheel circumference from the text input (parsed as float)
    def get_wheel_circumference(self) -> float:
        """Return the wheel circumference value (default 2.0 m)."""
        try:
            return float(self._wheel_input.text())
        except ValueError:
            return 2.0

    # Read and return the connection timeout from the text input (parsed as int)
    def get_connection_timeout(self) -> int:
        """Return the connection timeout in ms (default 3000)."""
        try:
            return int(self._timeout_input.text())
        except ValueError:
            return 3000

    # Return whether the "Log Warnings" toggle switch is checked
    def get_warnings_enabled(self) -> bool:
        """Return whether log-warnings toggle is checked."""
        return self._warn_toggle.is_checked()

    # Return whether the "Debug Values" toggle switch is checked
    def get_debug_enabled(self) -> bool:
        """Return whether debug-values toggle is checked."""
        return self._debug_toggle.is_checked()

    # Mark the time as having been manually set by the user
    def _on_time_changed(self):
        self._time_set = True

    # Return whether the target time has been explicitly set
    def is_time_set(self):
        return self._time_set

    # Override the time-set flag externally
    def set_time_set(self, val: bool):
        self._time_set = val

    # Set the time editor to the current wall-clock time and update the display
    def _set_current_time(self):
        self._time_edit.setTime(QTime.currentTime())
        self._start_display.setText(QTime.currentTime().toString("HH:mm:ss"))
        self._time_set = True

    # Return the QTime value from the time editor
    def get_target_time(self) -> QTime:
        """Return the target time from the QTimeEdit."""
        return self._time_edit.time()

    # Return a dictionary of all alarm threshold values and the enabled flag
    def get_alarm_values(self) -> dict:
        """Return a dict of alarm thresholds (engine, battery, chip, battery_pct) and enabled flag."""
        return {
            "engine": self._alarm_engine.value() or 100,
            "battery": self._alarm_battery_temp.value() or 60,
            "chip": self._alarm_chip.value() or 80,
            "battery_pct": self._alarm_battery_pct.value() or 20,
            "enabled": self._alarm_toggle.isChecked(),
        }

    # Update the displayed start-time text
    def set_start_display(self, text: str):
        """Update the displayed start time string."""
        self._start_display.setText(text)

    # Update the serial port label text
    def set_port_label(self, port: str):
        """Update the serial port label."""
        self._port_label.setText(port)

    # Update the CSV filename label text
    def set_csv_label(self, name: str):
        self._csv_label.setText(name)

    # Callback invoked when the user clicks Connect/Disconnect — set externally by sidebar
    _on_connect = None

    # Scan for available serial ports and populate the combo box
    def _refresh_ports(self):
        self._port_combo.clear()
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            if not ports:
                self._port_combo.addItem("(no ports found)")
            else:
                for p in ports:
                    self._port_combo.addItem(p.device, p.device)
        except ImportError:
            self._port_combo.addItem("(pyserial not available)")

    # Handle Connect/Disconnect button click
    def _on_connect_clicked(self):
        port = self._port_combo.currentData()
        if port and self._on_connect:
            self._on_connect(port)

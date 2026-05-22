"""Right sidebar layout for C.R.O.N.O.S. OS.

Contains the settings panel, multi-tab log output (Log / Serial / Errors),
and the command-line interface.  The command dispatcher routes text
commands to individual ``_cmd_*`` handlers that mutate settings or
control the serial connection.
"""

# Import all Qt widgets needed for the sidebar: containers, frames, text displays, tab widget, scroll area, and input fields
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QTextEdit, QLineEdit, QTabWidget, QScrollArea
# Import Qt enums for scroll-bar policies, cursor shapes, alignment, and key codes
from PySide6.QtCore import Qt

# Import the settings panel that exposes alarm limits, round/wheel config, and toggle switches
from ui.panels.settings_panel import SettingsPanel


# Semi-transparent dark card style with a subtle cyan border, matching the HUD theme of the dashboard
_CARD_STYLE = """
QFrame#SidebarCard {
    background-color: rgba(15, 25, 45, 0.55);
    border: 1px solid rgba(0, 191, 255, 0.15);
    border-radius: 10px;
}
"""


# Command-to-description mapping shown by the "help" command so the operator knows what each command does
_COMMANDS = {
    "help": "Show available commands",
    "clear": "Clear the log",
    "reset": "Reset all values and clear the log",
    "time <HH:MM:SS>": "Set target time",
    "alarm engine|battery|chip|battery_pct <N>": "Set alarm limits (temps °C, battery %)",
    "alarms on|off": "Toggle alarm system",
    "sound on|off": "Toggle system sound",
    "alerts on|off": "Toggle alarm alerts",
    "warnings on|off": "Toggle log warnings",
    "debug on|off": "Toggle demo debug values",
    "round <km>": "Set round length in km",
    "wheel <m>": "Set wheel circumference in meters",
    "timeout <ms>": "Set connection timeout in ms",
    "list ports": "List available serial ports",
    "connect <port>": "Connect to a serial port (e.g. /dev/ttyUSB0)",
    "csv path": "Show CSV log file path",
    "csv lines": "Show number of lines logged in CSV",
    "csv new <name>": "Create a new CSV log file",
    "status": "Show current system status",
    "diag": "Dump current transmitted data values",
}

# Sorted list of command prefixes used for Tab-completion in the command-line widget
_TAB_COMMANDS = sorted(["help", "clear", "reset", "time", "alarm", "alarms", "sound", "alerts", "warnings", "debug", "round", "wheel", "timeout", "list", "connect", "csv", "status", "diag"])


class CommandLineEdit(QLineEdit):
    """Command input with Tab-completion and Up/Down history navigation.

    Overrides ``keyPressEvent`` to intercept Tab (cycle suggestions),
    Up (walk history backward), and Down (walk history forward / clear).
    Tab-completion candidates come from ``_TAB_COMMANDS``.
    """

    def __init__(self, parent=None):
        """Initialise empty history, Tab state, and command index."""
        # Initialise QLineEdit base to get text-input, placeholder, and signal support
        super().__init__(parent)
        # Ring buffer of previously entered commands for Up/Down recall
        self._history = []
        # Current position in the history ring; -1 means "not browsing history"
        self._history_index = -1
        # Current position in the Tab-completion cycle; -1 means "no cycle active"
        self._tab_index = -1
        # List of matching command strings for the current Tab-completion cycle
        self._tab_matches = []

    def focusNextPrevChild(self, _next):
        """Suppress Qt focus-advance so Tab is handled by the widget."""
        # Return False so pressing Tab doesn't move focus to the next widget — Tab is reserved for completion
        return False

    def keyPressEvent(self, event):
        """Intercept Tab, Up, Down; delegate all other keys to ``QLineEdit``.

        Tab cycles through matching command prefixes (or shows all commands
        when the line is empty).  Up/Down traverse the command history.
        """
        # Handle Tab key: cycle through command completions
        if event.key() == Qt.Key.Key_Tab:
            # If a completion cycle is already active, advance to the next match
            if self._tab_matches:
                self._tab_index = (self._tab_index + 1) % len(self._tab_matches)
                self.setText(self._tab_matches[self._tab_index])
                return
            # Get the current input text to find matching commands
            txt = self.text().strip()
            if not txt:
                # Empty input: show all available commands
                matches = _TAB_COMMANDS[:]
            else:
                # Filter commands that start with the typed prefix (case-insensitive)
                matches = [c for c in _TAB_COMMANDS if c.startswith(txt.lower())]
            if not matches:
                # No match found — do nothing, keep current input
                return
            # Store matches and set the first one as the current input text
            self._tab_matches = matches
            self._tab_index = 0
            self.setText(matches[0])
            return
        # Reset Tab state on any non-Tab key press so a fresh completion starts next time
        self._tab_index = -1
        self._tab_matches = []

        # Handle Up arrow: walk backward through command history
        if event.key() == Qt.Key.Key_Up:
            if self._history and self._history_index > -1:
                # Move one step back in history and show that command
                self._history_index -= 1
                self.setText(self._history[self._history_index])
            elif self._history:
                # At the start of history (or after a clear): jump to the last (most recent) entry
                self._history_index = len(self._history) - 1
                self.setText(self._history[self._history_index])
            return
        # Handle Down arrow: walk forward through command history
        if event.key() == Qt.Key.Key_Down:
            if self._history_index < len(self._history) - 1:
                # Move one step forward in history
                self._history_index += 1
                self.setText(self._history[self._history_index])
            else:
                # Past the last entry: clear the input field for a fresh command
                self._history_index = len(self._history)
                self.clear()
            return
        # For any other key, let QLineEdit handle it normally (typing, backspace, etc.)
        super().keyPressEvent(event)

    def add_history(self, cmd: str):
        """Append *cmd* to the history ring if it differs from the last entry."""
        # Avoid duplicate consecutive entries in the history ring
        if cmd and (not self._history or self._history[-1] != cmd):
            self._history.append(cmd)
        # Reset the history index so the next Up press starts from the end
        self._history_index = len(self._history)


class RightSidebar(QWidget):
    """Right-side panel: settings card, log tabs, and command-line console.

    Widget hierarchy::

        RightSidebar
        ├── QScrollArea (settings)
        │   └── QFrame#SidebarCard
        │       └── SettingsPanel
        └── QScrollArea (log)
            └── QFrame#SidebarCard
                ├── QTabWidget (Log / Serial / Errors)
                └── CommandLineEdit
    """

    def __init__(self, parent=None):
        # Initialise QWidget base so the sidebar can be added to the main view layout
        super().__init__(parent)
        # Tag the widget for QSS styling so the sidebar gets its own background and border treatment
        self.setObjectName("Sidebar")
        # Placeholder for the SerialReader instance; set externally via connect command
        self._reader = None
        # Placeholder for the TransmittedData reference; set externally so commands can mutate serial state
        self._td = None
        # Placeholder for a reset callback; set externally so the "reset" command can clear system state
        self._reset_callback = None

        # Root vertical layout for the entire sidebar — stacks settings scroll area and log scroll area
        layout = QVBoxLayout(self)
        # Set margins so content doesn't touch the sidebar edges
        layout.setContentsMargins(8, 8, 8, 8)
        # Set spacing between the settings card and the log card
        layout.setSpacing(8)

        # Create a scroll area for the settings panel so it doesn't take up too much vertical space
        scroll_settings = QScrollArea()
        # Allow the scroll area to resize its child widget automatically when the area is resized
        scroll_settings.setWidgetResizable(True)
        # Tag the scroll area for QSS styling
        scroll_settings.setObjectName("SettingsScroll")
        # Remove any frame border so the scroll area visually merges with the sidebar background
        scroll_settings.setFrameShape(QFrame.NoFrame)
        # Disable the horizontal scrollbar since the settings card has a fixed width
        scroll_settings.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Create a card frame that wraps the settings panel with the semi-transparent HUD style
        card = QFrame()
        card.setObjectName("SidebarCard")
        card.setStyleSheet(_CARD_STYLE)
        # Vertical layout inside the card for the settings panel
        cl = QVBoxLayout(card)
        cl.setContentsMargins(8, 8, 8, 8)
        cl.setSpacing(6)

        # Build the settings panel with default tab index 0
        self._settings = SettingsPanel(index=0)
        # Clear the panel's own stylesheet so it inherits the SidebarCard styling instead
        self._settings.setStyleSheet("")
        # Wire the settings panel's connect button to our port connection handler
        self._settings._on_connect = self.connect_to_port
        cl.addWidget(self._settings)
        # Install the card as the scroll area's widget
        scroll_settings.setWidget(card)
        # Add the settings scroll area to the sidebar layout with stretch factor 1
        layout.addWidget(scroll_settings, 1)

        # Create a scroll area for the log tabs and command input
        scroll_log = QScrollArea()
        scroll_log.setWidgetResizable(True)
        scroll_log.setObjectName("LogScroll")
        scroll_log.setFrameShape(QFrame.NoFrame)
        scroll_log.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Create the log card frame with the same semi-transparent HUD style
        log_card = QFrame()
        log_card.setObjectName("SidebarCard")
        log_card.setStyleSheet(_CARD_STYLE)
        # Vertical layout inside the log card: tabs on top, command input at the bottom
        ll = QVBoxLayout(log_card)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(0)

        # Create a tab widget with three tabs: Log, Serial (hidden by default), Errors
        self._tabs = QTabWidget()
        self._tabs.setObjectName("LogTabs")
        # Prevent the tab bar from expanding to fill all width — keep tabs compact
        self._tabs.tabBar().setExpanding(False)
        # Use document mode so tabs have a flat, frameless appearance matching the HUD style
        self._tabs.setDocumentMode(True)

        # Log tab: main text area for system messages, command output, and telemetry info
        self._log = QTextEdit()
        self._log.setObjectName("LogOutput")
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(100)
        self._tabs.addTab(self._log, "Log")

        # Serial tab: raw serial data output, always visible like a serial terminal monitor
        self._serial_log = QTextEdit()
        self._serial_log.setObjectName("LogOutput")
        self._serial_log.setReadOnly(True)
        self._serial_log.setMinimumHeight(100)
        self._tabs.addTab(self._serial_log, "Serial")
        # Serial tab is always visible — shows raw incoming data in terminal style

        # Errors tab: error queue output showing timestamp, error code, and description
        self._error_log = QTextEdit()
        self._error_log.setObjectName("LogOutput")
        self._error_log.setReadOnly(True)
        self._error_log.setMinimumHeight(100)
        self._tabs.addTab(self._error_log, "Errors")

        # Add the tab widget to the log card layout
        ll.addWidget(self._tabs)

        # Command input widget at the bottom of the log card
        self._cmd = CommandLineEdit()
        self._cmd.setObjectName("CommandInput")
        # Placeholder text to hint at the command prompt
        self._cmd.setPlaceholderText("> type command...")
        # Connect Enter/Return to the command dispatch handler
        self._cmd.returnPressed.connect(self._execute)
        ll.addWidget(self._cmd)

        # Install the log card as the scroll area's widget
        scroll_log.setWidget(log_card)
        # Add the log scroll area to the sidebar layout with stretch factor 1
        layout.addWidget(scroll_log, 1)

        # Write initial system messages so the operator knows the dashboard is alive
        self._log.append("[SYSTEM] C.R.O.N.O.S. OS initialized")
        self._log.append("[INFO] Telemetry dashboard ready")
        self._log.append("[INFO] Waiting for serial data...")
        self._log.append("[INFO] Type 'help' for available commands")

    def append_log(self, msg, color=None):
        """Append a plain or HTML-coloured message to the Log tab."""
        if color:
            # Insert the message with an inline color span so important messages stand out visually
            self._log.textCursor().insertHtml(
                f'<span style="color:{color};">{msg}</span><br>'
            )
            # Auto-scroll to the bottom so the newest message is always visible
            sb = self._log.verticalScrollBar()
            sb.setValue(sb.maximum())
        else:
            # Plain text append, which QTextEdit auto-scrolls by default
            self._log.append(msg)

    def append_serial(self, msg):
        """Append a cyan-coloured message to the Serial tab."""
        # Insert the raw serial line with the signature cyan colour so it's visually distinct
        self._serial_log.textCursor().insertHtml(
            f'<span style="color:rgba(0,191,255,0.8);">{msg}</span><br>'
        )
        # Auto-scroll to the bottom so the newest serial data is always visible
        sb = self._serial_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_error_queue(self, queue):
        """Clear and repopulate the Errors tab from *queue* (list of error tuples)."""
        # Clear the existing error log before repopulating to avoid duplicating entries
        self._error_log.clear()
        from datetime import datetime
        for ts, code, name, desc in queue:
            tstr = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            # Colour positive error codes red and zero/negative (ok/resolved) green for quick status scanning
            color = "#ff5050" if code > 0 else "#00ff88"
            self._error_log.textCursor().insertHtml(
                f'<span style="color:{color};">[{tstr}] ERR {code}  {name}</span><br>'
            )
        # Auto-scroll to the bottom so the newest error is visible
        sb = self._error_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def set_serial_tab_visible(self, visible: bool):
        """No-op — Serial tab is always visible now (shows raw data like a terminal)."""

    @property
    def raw_queue(self):
        """Return the active reader's raw data queue, or None."""
        return self._reader.raw_queue if self._reader else None

    def connect_to_port(self, port: str):
        """Connect to *port*, stop any existing reader, and start a new SerialReader."""
        from core.serial_background_reading import SerialReader
        from core.csv_logger import csv_logger
        if self._reader:
            try:
                self._reader.stop()
            except Exception:
                pass
        csv_logger.close()
        td = self._td
        try:
            self._reader = SerialReader(port, td, 115200)
            self._reader.start()
            csv_logger.open()
            self._settings.set_csv_label(csv_logger.basename)
            self._settings.set_port_label(port)
            self._log.append(f"[OK] Connected to {port}")
            self._log.append(f"[OK] Logging to {csv_logger.path}")
            self._serial_log.append(f"--- Connected to {port} ---")
        except Exception as e:
            self._reader = None
            self._log.append(f"[!] Failed to connect: {e}")

    def _execute(self):
        """Parse the current command text and dispatch to the matching handler.

        The first whitespace-delimited token is looked up in a handler dict;
        remaining tokens are passed as ``args``.  Commands are case-insensitive.
        """
        # Capture and clear the input immediately so the operator sees a clean field
        raw = self._cmd.text().strip()
        self._cmd.clear()
        # Ignore empty input to avoid spurious log entries
        if not raw:
            return
        # Record the command in history for Up/Down recall
        self._cmd.add_history(raw)
        # Echo the command to the log so there's a record of what was executed
        self._log.append(f"> {raw}")
        # Split into command name (lowercased for case-insensitive matching) and arguments (preserve case)
        parts = raw.split()
        cmd = parts[0].lower()
        args = parts[1:]

        # Dispatch table mapping command names to their handler methods
        handler = {
            "help": self._cmd_help,
            "clear": self._cmd_clear,
            "reset": self._cmd_reset,
            "time": self._cmd_time,
            "alarm": self._cmd_alarm,
            "sound": self._cmd_sound,
            "alerts": self._cmd_alerts,
            "warnings": self._cmd_warnings,
            "debug": self._cmd_debug,
            "round": self._cmd_round,
            "wheel": self._cmd_wheel,
            "timeout": self._cmd_timeout,
            "alarms": self._cmd_alarms_toggle,
            "list": self._cmd_list,
            "connect": self._cmd_connect,
            "csv": self._cmd_csv,
            "status": self._cmd_status,
            "diag": self._cmd_diag,
        }.get(cmd)

        if handler:
            handler(args)
        else:
            self._log.append(f"[!] Unknown command '{cmd}' — type 'help' for available commands")

    def _cmd_help(self, args):
        """List every available command and its description."""
        self._log.append("Available commands:")
        for name, desc in _COMMANDS.items():
            self._log.append(f"  {name:<22}  {desc}")

    def _cmd_clear(self, args):
        """Clear the Log and Serial tab contents."""
        self._log.clear()
        self._serial_log.clear()

    def _cmd_reset(self, args):
        """Clear both logs and invoke the system reset callback."""
        self._log.clear()
        self._serial_log.clear()
        if self._reset_callback:
            self._reset_callback()
        self._log.append("[OK] System reset")

    def _cmd_time(self, args):
        """Set target countdown time via ``time <HH:MM:SS>``."""
        if not args:
            self._log.append("[!] Usage: time <HH:MM:SS>")
            return
        t = args[0]
        if len(t.split(":")) != 3:
            self._log.append("[!] Invalid format — use HH:MM:SS")
            return
        try:
            from PySide6.QtCore import QTime
            h, m, s = t.split(":")
            qt = QTime(int(h), int(m), int(s))
            # Update the settings panel's time edit and display label with the parsed time
            self._settings._time_edit.setTime(qt)
            self._settings._start_display.setText(t)
            self._log.append(f"[OK] Target time set to {t}")
        except ValueError:
            self._log.append("[!] Invalid time value")

    def _cmd_alarm(self, args):
        """Set an alarm threshold via ``alarm <engine|battery|chip|battery_pct> <N>``."""
        if len(args) != 2:
            self._log.append("[!] Usage: alarm <engine|battery|chip|battery_pct> <N>")
            return
        which, val = args[0], args[1]
        try:
            val = int(val)
        except ValueError:
            self._log.append("[!] Value must be a number")
            return
        # Map alarm names to the settings panel's alarm row widgets
        rows = {
            "engine": self._settings._alarm_engine,
            "battery": self._settings._alarm_battery_temp,
            "chip": self._settings._alarm_chip,
            "battery_pct": self._settings._alarm_battery_pct,
        }
        row = rows.get(which)
        if not row:
            self._log.append("[!] Unknown alarm — use engine, battery, chip, or battery_pct")
            return
        row.set_value(val)
        unit = "%" if which == "battery_pct" else "°C"
        self._log.append(f"[OK] {which.capitalize()} alarm limit set to {val}{unit}")

    def _cmd_alarms_toggle(self, args):
        """Enable / disable / toggle the alarm system via ``alarms on|off``."""
        state = args[0] if args else ""
        if state == "on":
            self._settings._alarm_toggle.setChecked(True)
            self._log.append("[OK] Alarm system ON")
        elif state == "off":
            self._settings._alarm_toggle.setChecked(False)
            self._log.append("[OK] Alarm system OFF")
        else:
            # Without an explicit on/off arg, flip the current state
            self._settings._alarm_toggle.setChecked(not self._settings._alarm_toggle.isChecked())
            self._log.append(f"[OK] Alarm system toggled {'ON' if self._settings._alarm_toggle.isChecked() else 'OFF'}")

    def _cmd_round(self, args):
        """Set round/track length via ``round <km>``."""
        if not args:
            self._log.append("[!] Usage: round <km>")
            return
        try:
            v = float(args[0])
            self._settings._round_input.setText(str(v))
            self._log.append(f"[OK] Round length set to {v} km")
        except ValueError:
            self._log.append("[!] Value must be a number")

    def _cmd_wheel(self, args):
        """Set wheel circumference via ``wheel <m>``."""
        if not args:
            self._log.append("[!] Usage: wheel <m>")
            return
        try:
            v = float(args[0])
            self._settings._wheel_input.setText(str(v))
            self._log.append(f"[OK] Wheel circumference set to {v} m")
        except ValueError:
            self._log.append("[!] Value must be a number")

    def _cmd_timeout(self, args):
        """Set connection timeout via ``timeout <ms>``."""
        if not args:
            self._log.append("[!] Usage: timeout <ms>")
            return
        try:
            v = int(args[0])
            self._settings._timeout_input.setText(str(v))
            self._log.append(f"[OK] Connection timeout set to {v} ms")
        except ValueError:
            self._log.append("[!] Value must be a number")

    def _cmd_sound(self, args):
        """Toggle system sound via ``sound on|off``."""
        from ui.components.check_button import ToggleSwitch
        # Find the first ToggleSwitch among the settings panel's children (the sound toggle)
        toggles = [c for c in self._settings.children() if isinstance(c, ToggleSwitch)]
        if not toggles:
            self._log.append("[!] Sound toggle not found")
            return
        state = args[0] if args else ""
        if state == "on":
            toggles[0].set_checked(True)
            self._log.append("[OK] System sound ON")
        elif state == "off":
            toggles[0].set_checked(False)
            self._log.append("[OK] System sound OFF")
        else:
            toggles[0].set_checked(not toggles[0].is_checked())
            self._log.append(f"[OK] System sound toggled {'ON' if toggles[0].is_checked() else 'OFF'}")

    def _cmd_alerts(self, args):
        """Toggle alarm alerts via ``alerts on|off``."""
        from ui.components.check_button import ToggleSwitch
        # Find all ToggleSwitches and pick the second one (index 1), which is the alerts toggle
        toggles = [c for c in self._settings.children() if isinstance(c, ToggleSwitch)]
        if len(toggles) < 2:
            self._log.append("[!] Alerts toggle not found")
            return
        t = toggles[1]
        state = args[0] if args else ""
        if state == "on":
            t.set_checked(True)
            self._log.append("[OK] Alerts ON")
        elif state == "off":
            t.set_checked(False)
            self._log.append("[OK] Alerts OFF")
        else:
            t.set_checked(not t.is_checked())
            self._log.append(f"[OK] Alerts toggled {'ON' if t.is_checked() else 'OFF'}")

    def _cmd_list(self, args):
        """List available USB/ACM serial ports via ``list ports``."""
        try:
            import serial.tools.list_ports
            all_ports = serial.tools.list_ports.comports()
            # Filter to only USB and ACM devices since those are the relevant serial port types for telemetry hardware
            ports = [p for p in all_ports if 'USB' in p.description or 'ACM' in p.description or 'ttyUSB' in p.device or 'ttyACM' in p.device]
            if not ports:
                self._log.append("[INFO] No devices connected")
                return
            self._log.append(f"Connected devices ({len(ports)}):")
            for p in sorted(ports, key=lambda x: x.device):
                self._log.append(f"  > {p.device}  ({p.description})")
        except ImportError:
            self._log.append("[!] pyserial not installed")

    def _cmd_connect(self, args):
        """Connect to a serial port via ``connect <port>`` (e.g. ``connect /dev/ttyUSB0``)."""
        if not args:
            self._log.append("[!] Usage: connect <port>  (e.g. connect /dev/ttyUSB0)")
            return
        self.connect_to_port(args[0])

    def _cmd_debug(self, args):
        """Toggle demo debug values via ``debug on|off``."""
        t = self._settings._debug_toggle
        state = args[0] if args else ""
        if state == "on":
            t.set_checked(True)
            self._log.append("[OK] Debug values ON")
        elif state == "off":
            t.set_checked(False)
            self._log.append("[OK] Debug values OFF")
        else:
            t.set_checked(not t.is_checked())
            self._log.append(f"[OK] Debug values toggled {'ON' if t.is_checked() else 'OFF'}")

    def _cmd_warnings(self, args):
        """Toggle log warnings via ``warnings on|off``."""
        t = self._settings._warn_toggle
        state = args[0] if args else ""
        if state == "on":
            t.set_checked(True)
            self._log.append("[OK] Log warnings ON")
        elif state == "off":
            t.set_checked(False)
            self._log.append("[OK] Log warnings OFF")
        else:
            t.set_checked(not t.is_checked())
            self._log.append(f"[OK] Log warnings toggled {'ON' if t.is_checked() else 'OFF'}")

    def _cmd_csv(self, args):
        """Query or manage the CSV logger via ``csv path|lines|new <name>``."""
        try:
            from core.csv_logger import csv_logger
        except ImportError:
            self._log.append("[!] CSV logger not available")
            return
        sub = args[0] if args else ""
        if sub == "path":
            self._log.append(f"CSV log: {csv_logger.path}")
        elif sub == "lines":
            self._log.append(f"CSV lines: {csv_logger.count}")
        elif sub == "new":
            if len(args) < 2:
                self._log.append("[!] Usage: csv new <filename>")
                return
            csv_logger.new_file(args[1])
            self._settings.set_csv_label(csv_logger.basename)
            self._log.append(f"[OK] New CSV log: {csv_logger.path}")
        else:
            self._log.append("[!] Usage: csv path|csv lines|csv new <name>")

    def _cmd_status(self, args):
        """Print current system state: time, target, alarms, round, wheel, serial."""
        from datetime import datetime
        now = datetime.now()
        t = self._settings.get_target_time()
        self._log.append(f"System time: {now.strftime('%H:%M:%S')}")
        self._log.append(f"Target time: {t.toString('HH:mm:ss')}")
        alarms = self._settings.get_alarm_values()
        self._log.append(f"Alarms: {'ON' if alarms['enabled'] else 'OFF'}")
        self._log.append(f"  Engine: {alarms['engine']}°C")
        self._log.append(f"  Battery Temp: {alarms['battery']}°C")
        self._log.append(f"  Chip: {alarms['chip']}°C")
        self._log.append(f"  Battery %: {alarms['battery_pct']}% (low)")
        self._log.append(f"Round: {self._settings.get_round_length()} km")
        self._log.append(f"Wheel: {self._settings.get_wheel_circumference()} m")
        self._log.append(f"Timeout: {self._settings.get_connection_timeout()} ms")
        self._log.append(f"Serial: {'Connected to ' + self._reader.port if self._reader else 'Disconnected'}")

    def _cmd_diag(self, args):
        """Dump current transmitted data values."""
        td = self._td
        if td is None:
            self._log.append("[!] No transmitted data reference")
            return
        with td.lock:
            self._log.append("── TransmittedData ──")
            self._log.append(f"  PKT#={td.packet_number}  prev={td.previous_packet_number}")
            self._log.append(f"  TS={td.timestamp}ms  prev={td.previous_packet_timestamp}ms")
            self._log.append(f"  status={td.status}  drive={td.drive}")
            self._log.append(f"  TE={td.temperature_engine}°C  TB={td.temperature_battery}°C  TC={td.temperature_chip}°C")
            self._log.append(f"  AX={td.lin_accel_x}  AY={td.lin_accel_y}")
            self._log.append(f"  euler={td.euler}  gyro_z={td.gyro_z}")
            self._log.append(f"  V={td.voltage}  I={td.current}  BV={td.battery_voltage}  BP={td.battery_percentage}%")
        if self._reader:
            self._log.append(f"  last_data_time: {self._reader.last_data_time}")
            self._log.append(f"  queue size: {self._reader.raw_queue.qsize()}")


def get_right_sidebar_layout():
    """Construct and return a fresh ``RightSidebar`` instance."""
    return RightSidebar()

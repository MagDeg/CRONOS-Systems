"""Main update loop — runs every 500 ms via QTimer.

Coordinates:
  1. Zero-out or demo-data generation when no serial reader is active.
  2. Connection-state detection and loss popup.
  3. DisplayDataCalculator update (raw → display transform).
  4. Serial debug output.
  5. Demo-／connected-mode data handling (velocity, distance, …).
  6. Delegated sub-system updates via tracking/* classes.
  7. Elapsed／remaining countdown time.
  8. Alarm / warning checks.
  9. MetricHistory and StatsTracker feed.
  10. Topbar popup refreshes.
"""

# Import math for mathematical operations used in calculations
import math
# Import time for timestamps, delta-time computation, and rate limiting between ticks
import time
# Import datetime to compute elapsed and remaining countdown time from a target clock time
from datetime import datetime

# Import the singleton MetricHistory ring buffer that feeds the trend graph popup
from data.metric_history import history
# Import the rolling statistics tracker that computes min/max/avg over a fixed-size sample window
from core.stats_tracker import StatsTracker
# Import all sub-system trackers that manage derived vehicle state
from tracking import PositionTracker, TripComputer, ErrorTracker, LapTimer, EnergyTracker


class TickLoop:
    """Top-level coordinator for the 500 ms telemetry tick.

    Owns all tracking sub-systems and dispatches to them each tick.
    The ``tick()`` method is connected to ``QTimer.timeout`` in main.py.
    """

    # Initialize the tick loop with references to all major data objects and the main window
    def __init__(self, window, transmitted, display, calculator, demo):
        # ── External references ──────────────────────────────────────
        # Keep a reference to the main window so we can trigger widget repaints and access sub-components
        self.window = window              # MainWindow
        # Keep a reference to the thread-safe raw data container updated by the serial reader background thread
        self.transmitted = transmitted    # TransmittedData (thread-safe)
        # Keep a mutable reference to the computed display data that drives all widget rendering
        self.display = display            # DisplayData (mutable)
        # Keep the calculator that transforms raw TransmittedData fields into DisplayData values
        self.calculator = calculator      # DisplayDataCalculator
        # Keep the demo data generator for producing synthetic telemetry when no serial port is connected
        self.demo = demo                  # DemoDataGenerator | None

        # ── Tracking sub-systems ─────────────────────────────────────
        # Create the position tracker that integrates velocity + heading into XY coordinates for the route view
        self.pos_tracker = PositionTracker()
        # Create the trip computer that tracks distance, average speed, and trip duration
        self.trip = TripComputer()
        # Create the error tracker that decodes the status-field bitmask and maintains a queue of active errors
        self.errors = ErrorTracker()
        # Create the lap timer that detects round crossings and records split / lap times
        self.lap_timer = LapTimer()
        # Create the energy tracker that integrates power over time to compute cumulative kWh consumption
        self.energy = EnergyTracker()

        # ── Per-tick state ───────────────────────────────────────────
        # Create a rolling statistics buffer of 50 samples for computing min/max/avg of telemetry metrics
        self.stats = StatsTracker(50)     # Rolling min／max／avg (50 samples)
        # Store the previous tick's velocity so we can compute acceleration via finite difference
        self._prev_velocity: float = 0.0
        # Store the previous tick's timestamp so we can compute the real delta-time between ticks (accounts for timer drift)
        self._prev_tick_time: float = time.time()
        # Track which warnings and alarms have already been logged to avoid spamming duplicate messages every tick
        self._warned: set[str] = set()
        # Track the previous debug toggle to detect transitions into and out of demo mode
        self._prev_debug: bool = True
        # Track the previous connection state to detect the rising edge of a disconnection
        self._prev_connected: bool = False

        # Wire the settings panel's reset button to the full system-reset method so the operator can clear all data
        window._main_view._right_sidebar._reset_callback = self._reset_system

    # ── Data-transform step ──────────────────────────────────────────
    # Lock the transmitted data, run the calculator, and push computed values to every widget
    def _update(self) -> None:
        """Lock transmitted data, run calculator, push to all widgets."""
        # Acquire the thread lock so we safely read fields that the serial-reader background thread may be writing
        with self.transmitted.lock:
            # Run all calculations that transform raw telemetry into display-ready values
            self.calculator.calculate_all_display_data()
        # Push the updated DisplayData to every widget in the dashboard so they repaint with the latest values
        self.window.update_all_widgets(self.display)

    # ── Full system reset ────────────────────────────────────────────
    # Zero out every data container and restore all trackers to their initial state
    def _reset_system(self) -> None:
        """Zero everything: transmitted data, display, trackers, stats."""
        # Acquire the lock so we can safely zero the raw data container shared with the serial reader thread
        with self.transmitted.lock:
            # Zero all integer-typed fields — packet counters, timestamps, and the status bitfield
            for f in ("packet_number", "previous_packet_number", "timestamp",
                      "previous_packet_timestamp", "status"):
                # Zero each integer field using setattr for concise bulk assignment
                setattr(self.transmitted, f, 0)
            # Zero engine temperature explicitly (handled separately from the generic loops above)
            self.transmitted.temperature_engine = 0
            # Zero battery temperature explicitly
            self.transmitted.temperature_battery = 0
            # Zero chip temperature explicitly
            self.transmitted.temperature_chip = 0
            # Zero all float-typed measurement fields — drive level, accelerations, voltage, current, battery
            for f in ("drive", "lin_accel_x", "lin_accel_y", "euler", "gyro_z",
                      "voltage", "current", "battery_voltage", "battery_percentage"):
                # Zero each float field using setattr
                setattr(self.transmitted, f, 0.0)

        # Reset every computed field in the display data model back to its default zero state
        self.display.reset()
        # Purge the metric history ring buffer so stale data from before the reset doesn't appear in trend graphs
        history.clear()
        # Replace the stats tracker with a fresh instance to clear all rolling min/max/avg samples
        self.stats = StatsTracker(50)
        # Clear the warning-deduplication set so alarms and warnings will fire again after the reset
        self._warned.clear()
        # Reset the previous-velocity stored state so acceleration calculations start from zero
        self._prev_velocity = 0.0

        # Reset the position tracker back to the coordinate origin
        self.pos_tracker.reset()
        # Reset the trip computer: zero distance, average speed, and trip duration
        self.trip.reset()
        # Clear all pending errors from the error tracker's queue
        self.errors.reset()
        # Reset lap timers, lap counts, and round-crossing state
        self.lap_timer.reset()

        # Reset the demo generator's artificial packet counter so synthetic data restarts from packet 0
        self.demo._packet_num = 0
        # Clear the "target time set" flag in settings so the countdown display resets to zero
        self.window._main_view._right_sidebar._settings.set_time_set(False)

    # ── Main tick ────────────────────────────────────────────────────
    # The heart of the dashboard update loop — called every 500 ms by QTimer
    def tick(self) -> None:
        """Called every 500 ms — the heart of the dashboard update loop."""
        # Grab shorthand references to frequently-accessed sub-components for conciseness in the rest of tick()
        sidebar = self.window._main_view._right_sidebar
        settings = sidebar._settings
        debug = settings.get_debug_enabled()
        rdr = sidebar._reader

        # ── 1. Data source ───────────────────────────────────────────
        # When no serial reader exists, decide whether to run demo mode or zero out all fields
        if rdr is None:
            if debug:
                # Demo mode is active — generate one tick of synthetic telemetry
                self.demo.tick()
            else:
                # No reader and no demo — zero all raw fields so widgets show safe default values
                with self.transmitted.lock:
                    # Zero integer fields: packet counters, timestamps, and the status code
                    for f in ("packet_number", "previous_packet_number",
                              "timestamp", "previous_packet_timestamp", "status"):
                        setattr(self.transmitted, f, 0)
                    # Zero all three temperature readings
                    self.transmitted.temperature_engine = 0
                    self.transmitted.temperature_battery = 0
                    self.transmitted.temperature_chip = 0
                    # Zero all float measurement fields
                    for f in ("drive", "lin_accel_x", "lin_accel_y", "euler",
                              "gyro_z", "voltage", "current",
                              "battery_voltage", "battery_percentage"):
                        setattr(self.transmitted, f, 0.0)

        # ── 2. Connection state ──────────────────────────────────────
        # Determine whether the serial link is alive based on time since last received data
        if rdr is not None:
            timeout_ms = settings.get_connection_timeout()
            # The connection is considered alive if less than the configured timeout has elapsed since the last valid packet
            self.display.connection_state = (
                (time.time() - rdr.last_data_time) * 1000 < timeout_ms
            )
        elif debug:
            # In demo mode there is no real connection, but we report connected so all downstream systems keep working
            self.display.connection_state = True
        else:
            # No reader and not in demo mode means definitively disconnected
            self.display.connection_state = False

        # Detect the transition from connected → disconnected and show a one-time warning popup
        if self._prev_connected and not self.display.connection_state:
            # Lazily import QMessageBox to avoid paying the import cost when no disconnection ever occurs
            from PySide6.QtWidgets import QMessageBox
            # Create a non-modal message box parented to the main window
            msg = QMessageBox(self.window)
            # Set the icon to Warning for immediate visual recognition of a problem
            msg.setIcon(QMessageBox.Warning)
            # Give the popup a clear, descriptive title
            msg.setWindowTitle("Connection Lost")
            # Explain exactly what happened so the operator can diagnose the issue
            msg.setText("Serial connection lost — no data received within timeout.")
            # Provide a single OK button so the operator can acknowledge and dismiss the popup
            msg.setStandardButtons(QMessageBox.Ok)
            # Show the dialog non-modally so it does not block the live dashboard display
            msg.show()
            # Clear all warning flags so that after reconnection, every alarm and warning is re-emitted fresh
            self._warned.clear()
        # Save the current connection state for edge detection on the next tick
        self._prev_connected = self.display.connection_state

        # ── 3. Compute display values ────────────────────────────────
        # Lock transmitted data, run the calculator, and push the resulting DisplayData to every widget
        self._update()

        # ── 4. Raw serial monitor ────────────────────────────────────
        # Drain raw serial lines from the reader's thread-safe queue into the Serial tab
        import queue as _queue
        raw_queue = sidebar.raw_queue
        if raw_queue is not None:
            while True:
                try:
                    raw_line = raw_queue.get_nowait()
                    sidebar.append_serial(raw_line)
                except _queue.Empty:
                    break

        # ── 5. Formatted debug output ─────────────────────────────────
        if debug:
            # Lock the raw data to safely format a debug line from all current field values
            with self.transmitted.lock:
                t = self.transmitted
                # Build a single-line dump of every raw telemetry field
                line = (
                    f"PKT#{t.packet_number} T{t.timestamp}ms "
                    f"DRV={t.drive:.0f} "
                    f"TE={t.temperature_engine}°C TB={t.temperature_battery}°C "
                    f"TC={t.temperature_chip}°C "
                    f"AX={t.lin_accel_x:.1f} AY={t.lin_accel_y:.1f} "
                    f"V={t.voltage:.2f}V I={t.current:.2f}A "
                    f"BV={t.battery_voltage:.2f}V BP={t.battery_percentage:.0f}%"
                    f" status={t.status}"
                )
            # Append the formatted line to the Log tab with a [DBG] prefix
            sidebar.append_log(f"[DBG] {line}")

        # ── 6. Demo-off transition (clear everything) ────────────────
        # Detect when the operator switches from demo mode off — purge all demo-derived data so it doesn't pollute the display
        if not debug and self._prev_debug:
            history.clear()
            self.display.distance = 0.0
            self.display.estimated_rounds = 0.0
            self.display.energy_kwh = 0.0
            self.stats = StatsTracker(50)
            self.pos_tracker.reset()
            self.trip.reset()
            self.errors.reset()
            self.lap_timer.reset()
        # Save the current debug state so we can detect the transition on the next tick
        self._prev_debug = debug

        # ── 7. Velocity & distance ───────────────────────────────────
        # Generate or zero RPM depending on the active data source
        if debug:
            # In demo mode, produce a random RPM to simulate a running engine
            import random
            self.display.rpm = random.uniform(500, 6000)
        elif rdr is None:
            # No serial connection and not in demo mode — the vehicle is off, RPM is zero
            self.display.rpm = 0.0
            # Reset previous velocity so the dashboard does not show stale movement from before the disconnect
            self._prev_velocity = 0.0

        # Read the user-configured wheel circumference in meters from the settings panel
        circ = settings.get_wheel_circumference()
        # Convert RPM to km/h: velocity = RPM * circumference(m) * 0.06 (where 0.06 = 60 min/h / 1000 m/km)
        self.display.velocity = self.display.rpm * circ * 0.06

        # Capture the current wall time for computing the real delta-time between ticks
        now = time.time()
        dt = now - self._prev_tick_time
        self._prev_tick_time = now
        # Use the average of current and previous velocity over the tick interval for more accurate trapezoidal distance integration
        avg_v = (self.display.velocity + self._prev_velocity) / 2
        self._prev_velocity = self.display.velocity
        # Integrate: distance += avg_kmh / 3600 s/h * dt_s → accumulates total distance in km
        self.display.distance += avg_v / 3600.0 * dt
        # Read the user-configured track round length in km
        rl = settings.get_round_length()
        # Estimate completed rounds; guard against division by zero if round length hasn't been configured yet
        self.display.estimated_rounds = self.display.distance / rl if rl > 0 else 0

        # ── 8. Delegated sub-system updates ──────────────────────────
        # Feed the energy tracker with delta-time and power so it can integrate kWh consumption
        self.energy.tick(dt, self.display.power, self.display)
        # Feed the trip computer with delta-time and velocity to update trip distance and averages
        self.trip.tick(dt, self.display.velocity, self.display)
        # Feed the lap timer with the current estimated round count to detect lap crossings
        self.lap_timer.tick(self.display.estimated_rounds, self.display)

        # Only integrate position when a live connection exists — prevents coordinate drift during disconnection
        if self.display.connection_state:
            self.pos_tracker.tick(dt, self.display.velocity, self.display.heading)

        # Push the position tracker's accumulated path and current location to the topbar route / minimap widget
        self.window._topbar.update_route(
            self.pos_tracker.get_path(),
            self.pos_tracker.pos_x,
            self.pos_tracker.pos_y,
            self.display.heading,
        )

        # ── 9. Countdown (elapsed／remaining time) ───────────────────
        # If the operator has set a target start time, compute elapsed and remaining time against the wall clock
        if settings.is_time_set():
            target = settings.get_target_time()
            now_dt = datetime.now()
            # Convert both target and now to total seconds since midnight for simple subtraction
            target_sec = target.hour() * 3600 + target.minute() * 60 + target.second()
            now_sec = now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second
            elapsed_sec = now_sec - target_sec
            # If the target is in the future (elapsed is negative), wrap by adding 24 hours for a count-up-from-zero feel
            if elapsed_sec < 0:
                elapsed_sec += 86400
            # Store elapsed time in milliseconds for the countdown display widget
            self.display.elapsed_time = elapsed_sec * 1000
            # Remaining time is the rest of the 24-hour window, clamped to zero
            self.display.remaining_time = max(0, 86400000 - self.display.elapsed_time)
        else:
            # No target has been set — zero out both displays
            self.display.elapsed_time = 0
            self.display.remaining_time = 0

        # ── 10. Alarm / warning engine ───────────────────────────────
        # Read the operator-configured alarm thresholds from the settings panel
        alarms = settings.get_alarm_values()
        # Only evaluate alarms when the alarm system is armed, warnings are enabled, and we have live data
        if alarms["enabled"] and settings.get_warnings_enabled() and self.display.connection_state:
            log = sidebar.append_log
            d = self.display
            # Each check: (display name, current value, threshold, unit, optional reverse flag)
            checks = [
                ("Engine", d.temperature_engine, alarms["engine"], "°C"),
                ("Battery", d.temperature_battery, alarms["battery"], "°C"),
                ("Chip", d.temperature_chip, alarms["chip"], "°C"),
                ("Battery %", d.battery_pct, alarms["battery_pct"], "%", True),
            ]
            for name, val, limit, unit, *_extra in checks:
                reverse = _extra[0] if _extra else False
                key_a = f"{name}_alarm"
                key_w = f"{name}_warn"
                if reverse:
                    # For metrics where lower is worse (e.g., battery percentage), alarm when at or below the limit
                    alarm = val <= limit
                    warn = val <= limit * 1.15
                else:
                    # For metrics where higher is worse (e.g., temperatures), alarm when at or above the limit
                    alarm = val >= limit
                    warn = val >= limit * 0.85
                if alarm:
                    # Only log the alarm once — avoid spamming the log every 500 ms
                    if key_a not in self._warned:
                        log(f"[ALARM] {name} {val}{unit} "
                            f"{'below' if reverse else 'exceeds'} limit {limit}{unit}", "#ff5050")
                        self._warned.add(key_a)
                    # A fired alarm supersedes any pending warning for the same metric
                    self._warned.discard(key_w)
                elif warn:
                    # Only log the warning once
                    if key_w not in self._warned:
                        log(f"[WARN] {name} {val}{unit} "
                            f"{'approaching' if not reverse else 'near'} limit {limit}{unit}", "#ffcc00")
                        self._warned.add(key_w)
                    self._warned.discard(key_a)
                else:
                    # Value is within the safe range — clear both alarm and warning flags
                    self._warned.discard(key_a)
                    self._warned.discard(key_w)

        # ── 11. Error queue ──────────────────────────────────────────
        # Read the status field from the raw data under lock, then let the error tracker decode any error codes
        with self.transmitted.lock:
            status = self.transmitted.status
        self.errors.tick(status)
        sidebar.update_error_queue(self.errors.queue)
        self.window._topbar.update_module_status(self.errors.queue)

        # ── 12. Topbar popup refreshes ───────────────────────────────
        # Refresh the gyroscope / attitude popup with the latest orientation and acceleration data
        self.window._topbar.update_gyro(self.display)
        # Refresh the trip computer popup with updated distance, speed, and trip statistics
        self.window._topbar.update_trip(self.display)
        # Refresh the trend graph popup so it pulls in the latest data from MetricHistory
        self.window._topbar.update_trends()

        # ── 13. History feed (for trend graphs) ──────────────────────
        d = self.display
        # Record a timestamped snapshot of every key telemetry metric into the ring buffer for trend visualization
        history.feed(time.time(), {
            "velocity": d.velocity, "rpm": d.rpm,
            "voltage": d.voltage, "voltage_battery": d.voltage_battery,
            "battery_pct": d.battery_pct,
            "current": d.current, "power": d.power,
            "temperature_battery": d.temperature_battery,
            "temperature_chip": d.temperature_chip,
            "temperature_engine": d.temperature_engine,
            "acceleration": d.acceleration, "g_force": d.g_force,
            "distance": d.distance, "estimated_rounds": d.estimated_rounds,
            "packet_loss": d.packet_loss, "delay": d.delay,
            "elapsed_time": d.elapsed_time, "remaining_time": d.remaining_time,
        })

        # ── 14. StatsTracker feed ────────────────────────────────────
        s = self.stats
        # Feed every key telemetry value into the rolling statistics tracker to keep min/max/avg up to date
        s.feed("g_force", d.g_force)
        s.feed("delay", float(d.delay))
        s.feed("packet_loss", d.packet_loss)
        s.feed("voltage", d.voltage)
        s.feed("current", d.current)
        s.feed("power", d.power)
        s.feed("velocity", d.velocity)
        s.feed("rpm", d.rpm)
        s.feed("temp_battery", float(d.temperature_battery))
        s.feed("temp_chip", float(d.temperature_chip))
        s.feed("temp_engine", float(d.temperature_engine))
        s.feed("acceleration", d.acceleration)

        # ── 15. Publish rolling stats to DisplayData ─────────────────
        # Copy every computed rolling statistic back into DisplayData so the widgets can render min/max/avg values
        d.acceleration_avg = s.avg("acceleration")
        d.acceleration_min = s.min("acceleration")
        d.acceleration_max = s.max("acceleration")
        d.gforce_avg = s.avg("g_force")
        d.gforce_min = s.min("g_force")
        d.gforce_max = s.max("g_force")
        d.delay_avg = s.avg("delay")
        d.delay_min = s.min("delay")
        d.delay_max = s.max("delay")
        d.packet_loss_avg = s.avg("packet_loss")
        d.packet_loss_min = s.min("packet_loss")
        d.packet_loss_max = s.max("packet_loss")
        d.voltage_avg = s.avg("voltage")
        d.voltage_min = s.min("voltage")
        d.voltage_max = s.max("voltage")
        d.current_avg = s.avg("current")
        d.current_min = s.min("current")
        d.current_max = s.max("current")
        d.power_avg = s.avg("power")
        d.power_min = s.min("power")
        d.power_max = s.max("power")
        d.velocity_avg = s.avg("velocity")
        d.velocity_min = s.min("velocity")
        d.velocity_max = s.max("velocity")
        d.rpm_avg = s.avg("rpm")
        d.rpm_min = s.min("rpm")
        d.rpm_max = s.max("rpm")
        d.temp_battery_avg = s.avg("temp_battery")
        d.temp_battery_min = s.min("temp_battery")
        d.temp_battery_max = s.max("temp_battery")
        d.temp_chip_avg = s.avg("temp_chip")
        d.temp_chip_min = s.min("temp_chip")
        d.temp_chip_max = s.max("temp_chip")
        d.temp_engine_avg = s.avg("temp_engine")
        d.temp_engine_min = s.min("temp_engine")
        d.temp_engine_max = s.max("temp_engine")

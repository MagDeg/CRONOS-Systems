"""Generates realistic random telemetry for demo/offline mode.

When no serial device is detected on ``SERIAL_PORT``, the
:class:`DemoDataGenerator` populates a :class:`~data_structs.received_data.TransmittedData`
with synthetic values every tick.  Certain time windows inject specific
status codes so the HUD's error display can be visually verified.
"""

# time.time() for wall-clock references to simulate realistic timestamp deltas
import time
# random.uniform/randint for generating realistic telemetry value ranges
import random
# The shared telemetry struct that demo mode populates each tick
from data.received_data import TransmittedData

# Default serial device path — main.py checks this to decide real-vs-demo mode
SERIAL_PORT = "/dev/ttyUSB0"

# Dynamically check whether a given serial port is physically present on this system
def port_exists(p):
    # Lazy import: pyserial's port enumeration — avoid overhead when not needed
    import serial.tools.list_ports
    # Compare the requested path against all detected comports' device names
    return p in [x.device for x in serial.tools.list_ports.comports()]

# Synthetic telemetry generator used when no serial hardware is connected
class DemoDataGenerator:
    """Generates synthetic telemetry when no serial hardware is present.

    ``tick()`` populates the shared :class:`~data_structs.received_data.TransmittedData`
    with randomised values that mimic realistic flight profiles.  Certain
    time windows intentionally inject non-zero status codes so the HUD
    error-panel logic can be visually validated.

    Attributes:
        _td: Shared TransmittedData instance to populate.
        _start_time: ``time.time()`` reference for elapsed-time simulation.
        _packet_num: Monotonically incrementing synthetic packet counter.
    """
    # Hold a reference to the shared TransmittedData plus internal counters for synthetic generation
    def __init__(self, transmitted: TransmittedData):
        # Store the shared struct that tick() will populate under its lock
        self._td = transmitted
        # Record construction time so tick() can compute elapsed seconds since demo start
        self._start_time = time.time()
        # Monotonically incrementing synthetic packet counter, incremented each tick
        self._packet_num = 0

    # Called from the main timer — fills the shared TransmittedData with synthetic values
    def tick(self):
        # Snapshot wall clock once so all elapsed-time calculations in this tick are consistent
        now = time.time()
        # Increment the synthetic packet counter so packet-loss logic sees a valid sequence
        self._packet_num += 1
        # Acquire the thread lock — same struct could be read by SerialReader in production
        with self._td.lock:
            # Save the current packet number as previous so the packet-loss delta is always 1
            self._td.previous_packet_number = self._td.packet_number
            # Write the new synthetic packet number
            self._td.packet_number = self._packet_num
            # Save the current timestamp as previous so the delay calculation gets a real delta
            self._td.previous_packet_timestamp = self._td.timestamp
            # Synthetic timestamp = milliseconds since demo started
            self._td.timestamp = int((now - self._start_time) * 1000)
            # Elapsed seconds — used to trigger intentional error codes at specific times
            t = now - self._start_time
            # Window 30–35s: inject status=2 (e.g. "low battery") for HUD error-panel testing
            if 30 < t < 35:
                self._td.status = 2
            # Window 60–66s: inject status=6 for mid-session error display verification
            elif 60 < t < 66:
                self._td.status = 6
            # Window 90–93s: inject status=15 to exercise a different error severity
            elif 90 < t < 93:
                self._td.status = 15
            # Window 120–125s: inject status=7 for another error-code rendering check
            elif 120 < t < 125:
                self._td.status = 7
            # Window 150–153s: inject status=20 to verify error rendering near session end
            elif 150 < t < 153:
                self._td.status = 20
            # Default: status=0 means "all nominal, no errors"
            else:
                self._td.status = 0
            # Synthetic RPM/drive value in a realistic rocket-motor range (500–6000)
            self._td.drive = random.uniform(500, 6000)
            # Engine temp 30–95°C mimics a warm but not overheating motor
            self._td.temperature_engine = random.randint(30, 95)
            # Battery temp 15–45°C is the safe operating window for LiPo packs
            self._td.temperature_battery = random.randint(15, 45)
            # Chip temp 20–75°C covers cold start to steady-state operation
            self._td.temperature_chip = random.randint(20, 75)
            # Lateral acceleration X: ±10 m/s² simulates mild vibration and turns
            self._td.lin_accel_x = random.uniform(-10, 10)
            # Lateral acceleration Y: ±10 m/s² pairs with X for a 2D acceleration vector
            self._td.lin_accel_y = random.uniform(-10, 10)
            # Heading in degrees — full 0–360 range keeps the compass widget constantly moving
            self._td.euler = random.uniform(0, 360)
            # Yaw rate ±90°/s — visible as rapid heading changes on the gyro display
            self._td.gyro_z = random.uniform(-90, 90)
            # System voltage in the 11–13V range, typical of a 3S LiPo under load
            self._td.voltage = random.uniform(11.0, 13.0)
            # Current draw 0–10A simulates variable electrical load
            self._td.current = random.uniform(0, 10)
            # Separate battery voltage channel — may differ from system voltage due to regulation
            self._td.battery_voltage = random.uniform(11.0, 13.0)
            # Battery state-of-charge 0–100% for the fuel-gauge-style widget
            self._td.battery_percentage = random.uniform(0, 100)

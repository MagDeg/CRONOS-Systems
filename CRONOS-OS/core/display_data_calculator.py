"""Transforms raw TransmittedData into display-ready DisplayData.

Owns a reference to both a :class:`~data_structs.received_data.TransmittedData`
and a :class:`~data_structs.displayed_data.DisplayData` instance.
``calculate_all_display_data()`` reads the raw fields (under the
TransmittedData lock) and writes computed values into the DisplayData
struct — packet loss, acceleration, g-force, heading, RPM, power, delay,
temperatures, and voltages.
"""

# sqrt needed for Euclidean magnitude of the (ax, ay) acceleration vector
from math import sqrt

# DisplayData is the output model — the computed values we push to widgets each tick
from data.displayed_data import DisplayData
# TransmittedData is the raw input model populated by SerialReader or DemoDataGenerator
from data.received_data import TransmittedData


# Calculator called once per timer tick: reads raw fields and writes all derived display values
class DisplayDataCalculator:
    """Transforms a :class:`~data_structs.received_data.TransmittedData` into a
    :class:`~data_structs.displayed_data.DisplayData`.

    Call ``calculate_all_display_data()`` on each tick — it reads raw
    fields (caller should hold ``data_transmitted.lock`` for
    thread-safety) and populates every derived field in
    ``data_display``.

    Attributes:
        data_display: Mutable DisplayData instance to write into.
        data_transmitted: Shared TransmittedData instance to read from.
    """
    # Bind to output (display) and input (transmitted) data structs — fixed for app lifetime
    def __init__(self, data_out: DisplayData, data_in: TransmittedData):
        # Keep a reference to the mutable DisplayData that widgets read from
        self.data_display = data_out
        # Keep a reference to the shared TransmittedData read by SerialReader under a lock
        self.data_transmitted = data_in

    # Top-level entry point: run every derived-field computation in the correct order
    def calculate_all_display_data(self):
        # Compute packet-loss percentage from the gap between consecutive sequence numbers
        self._packet_loss()
        # Compute linear-acceleration magnitude from the IMU's X/Y components
        self._acceleration()
        # Convert m/s² acceleration to g-force — must run after _acceleration()
        self._g_force()
        # Derive compass heading from euler angle and yaw rate from gyro Z
        self._heading_and_gyro()
        # Map the drive field directly to RPM for the tachometer gauge
        self._rpm()
        # Calculate electrical power as V × I
        self._power()
        # Compute inter-packet delay from the onboard clock timestamps
        self._delay()
        # Forward all three temperature channels to the display struct
        self._temperatures()
        # Forward voltage readings and battery percentage to the display struct
        self._voltage()
        # Forward the current reading to the display struct
        self._current()

    # RPM is a direct passthrough — this protocol encodes RPM in the drive field
    def _rpm(self):
        self.data_display.rpm = self.data_transmitted.drive

    # Batch-copy all voltage-related fields so the display shows one coherent snapshot
    def _voltage(self):
        self.data_display.voltage = self.data_transmitted.voltage
        self.data_display.voltage_battery = self.data_transmitted.battery_voltage
        self.data_display.battery_pct = self.data_transmitted.battery_percentage

    # Current is a direct passthrough — no scaling or derivation needed
    def _current(self):
        self.data_display.current = self.data_transmitted.current

    # Batch-copy all three temperature channels so the thermal panel updates atomically
    def _temperatures(self):
        self.data_display.temperature_chip = self.data_transmitted.temperature_chip
        self.data_display.temperature_battery = self.data_transmitted.temperature_battery
        self.data_display.temperature_engine = self.data_transmitted.temperature_engine

    # Electrical power = voltage × current (P = V × I) derived from raw readings
    def _power(self):
        self.data_display.power = self.data_transmitted.voltage * self.data_transmitted.current

    # The IMU euler angle serves as compass heading; gyro Z is the yaw rate for the gyro widget
    def _heading_and_gyro(self):
        self.data_display.heading = self.data_transmitted.euler
        self.data_display.gyro_z_rate = self.data_transmitted.gyro_z

    # Inter-packet delay = difference between consecutive onboard-clock timestamps (ms)
    def _delay(self):
        self.data_display.delay = self.data_transmitted.timestamp - self.data_transmitted.previous_packet_timestamp

    # Packet-loss % = (expected - received) / expected × 100, based on sequence-number gaps
    def _packet_loss(self):
        # Expected = how many packets should have arrived since last tick (1 + gap)
        expected = self.data_transmitted.packet_number - self.data_transmitted.previous_packet_number + 1
        # Received = exactly 1 (this packet itself)
        received = 1
        # Guard against division by zero on the very first packet when expected could be 0
        self.data_display.packet_loss = ((expected - received) / expected * 100) if expected > 0 else 0.0

    # 2D acceleration magnitude from the IMU's linear-acceleration axes
    def _acceleration(self):
        # Read X-axis linear acceleration for the acceleration-vector display
        ax = self.data_transmitted.lin_accel_x
        # Read Y-axis linear acceleration for the acceleration-vector display
        ay = self.data_transmitted.lin_accel_y
        # Forward raw X component unchanged to the display struct
        self.data_display.lin_accel_x = ax
        # Forward raw Y component unchanged to the display struct
        self.data_display.lin_accel_y = ay
        # Magnitude = sqrt(ax² + ay²) — the total linear acceleration independent of direction
        self.data_display.acceleration = sqrt(ax**2 + ay**2)

    # Convert m/s² to Gs (1 G = 9.80665 m/s²) for the g-force gauge widget
    def _g_force(self):
        self.data_display.g_force = self.data_display.acceleration / 9.80665

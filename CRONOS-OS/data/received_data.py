"""Raw telemetry data received from the vehicle over serial.

This module defines the TransmittedData dataclass which holds all
fields parsed directly from incoming serial packets.  Every field
carries a default value so the struct can be safely read without a
live connection.

Threading notes
---------------
``lock`` (:class:`threading.Lock`) guards all field writes performed
by the background :class:`~serial_background_reading.SerialReader`
thread.  The main (GUI) thread should acquire the same lock before
reading any non-atomic field.
"""

# Import the dataclass tools so we can define a compact data-holder with defaults and a Lock field
from dataclasses import dataclass, field
# Import Lock so the serial-reader thread can synchronise writes to these fields with the GUI thread
from threading import Lock

# Decorate the class so Python auto-generates __init__, __repr__, etc. without boilerplate
@dataclass
class TransmittedData:
    """Raw telemetry fields parsed from a serial packet.

    Attributes:
        packet_number: Monotonically increasing packet ID from the vehicle.
        previous_packet_number: Packet number from the prior read (used for loss detection).
        timestamp: Millisecond timestamp of this packet.
        previous_packet_timestamp: Timestamp of the prior packet (used for delay calc).
        status: Bitmask / error-code field reported by the vehicle.
        drive: Throttle/drive value mapped to RPM.
        temperature_engine: Engine temperature in °C.
        temperature_battery: Battery temperature in °C.
        temperature_chip: On-board chip temperature in °C.
        lin_accel_x: Linear acceleration X-axis (m/s²).
        lin_accel_y: Linear acceleration Y-axis (m/s²).
        euler: Yaw / heading angle (degrees).
        gyro_z: Angular velocity around Z-axis (deg/s).
        voltage: Main bus voltage (V).
        current: Main bus current (A).
        battery_voltage: Dedicated battery voltage (V).
        battery_percentage: State-of-charge estimate (%).
        lock: threading.Lock guarding all field writes from the serial reader thread.
    """
    # Monotonically incrementing packet ID so the GUI can detect skipped packets
    packet_number: int = 0
    # Store the previous packet number so packet-loss calculations work across ticks
    previous_packet_number: int = 0
    # Millisecond timestamp from the vehicle so the GUI can compute inter-packet delay
    timestamp: int = 0
    # Keep the prior timestamp so delay calculation doesn't need an external cache
    previous_packet_timestamp: int = 0
    # Bitmask of active error codes — the GUI compares this against ERROR_MAP to show warnings
    status: int = 0

    # Scaled throttle/drive value mapped to RPM for the speed gauge and stats tracking
    drive: float = 0.0

    # Engine coolant or block temperature in °C for the temperature panel and overheat alerts
    temperature_engine: int = 0
    # High-voltage battery pack temperature in °C for thermal monitoring
    temperature_battery: int = 0
    # On-board microcontroller chip temperature in °C for system-health tracking
    temperature_chip: int = 0

    # Linear acceleration on the vehicle's X axis (m/s²) for g-force / accel displays
    lin_accel_x: float = 0.0
    # Linear acceleration on the vehicle's Y axis (m/s²) for lateral g-force displays
    lin_accel_y: float = 0.0
    # Yaw / heading angle in degrees for the compass/heading widget
    euler: float = 0.0
    # Angular velocity around the Z axis (deg/s) for the gyro popup and rotation-rate display
    gyro_z: float = 0.0

    # Main bus voltage in volts — fed to the power/energy tracker and voltage display
    voltage: float = 0.0
    # Main bus current in amps — combined with voltage to compute instantaneous power
    current: float = 0.0

    # Dedicated battery (e.g. 12 V aux) voltage for the battery-status panel
    battery_voltage: float = 0.0
    # State-of-charge estimate as a percentage for the battery gauge
    battery_percentage: float = 0.0

    # A per-instance Lock so the serial-reader thread can safely mutate fields while the GUI reads them
    lock: Lock = field(default_factory=Lock)

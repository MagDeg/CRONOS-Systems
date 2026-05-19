"""Computed display values derived from raw telemetry.

This module defines the DisplayData dataclass which holds every value
shown on the GUI — packet statistics (loss, delay), derived physical
quantities (acceleration, g-force, power), moving min/max/avg windows,
and a list of active error codes.

``reset()`` restores every field to its default, which is the
recommended way to clear the HUD between sessions.
"""

# Import the dataclass tools so we can define a rich data-holder with defaults and a mutable list field
from dataclasses import dataclass, field

# Decorate the class so Python auto-generates __init__, __repr__, etc. without boilerplate
@dataclass
class DisplayData:
    """Computed display values shown on the HUD.

    Attributes are a mix of pass-through raw fields, derived quantities
    (acceleration, g-force, power), rolling-window aggregates (avg/min/max
    for every major metric), and a ``list_with_errors`` field for active
    error codes.  ``reset()`` restores all fields to their defaults.

    Aggregates are updated each tick by :class:`~stats_tracker.StatsTracker`
    and written into the ``*_avg`` / ``*_min`` / ``*_max`` fields.
    """
    # Percentage of packets lost over the observation window — shown on the network panel
    packet_loss: float = 0.0
    # Milliseconds between the current and previous packet — used for latency monitoring
    delay: int = 0
    # Whether the serial link is currently active — drives the connection-status indicator
    connection_state: bool = False
    # Derived magnitude of linear acceleration (m/s²) for the accel/g-force panel
    acceleration: float = 0.0
    # Lateral g-force derived from lin_accel_y — displayed in the g-force widget
    g_force: float = 0.0
    # Total distance travelled in metres, accumulated by the trip computer
    distance: float = 0.0
    # Estimated number of laps completed, derived from distance / track-length setting
    estimated_rounds: float = 0.0
    # Current vehicle speed in m/s — fed to the speed gauge and stats tracker
    velocity: float = 0.0
    # Revolutions per minute derived from drive/RPM scaling — shown on the RPM gauge
    rpm: float = 0.0
    # Main bus voltage pass-through for the electrics panel
    voltage: float = 0.0
    # Auxiliary battery voltage pass-through for the battery-status display
    voltage_battery: float = 0.0
    # State-of-charge estimate pass-through for the battery percentage gauge
    battery_pct: float = 0.0
    # Main bus current pass-through for the electrics panel
    current: float = 0.0
    # Instantaneous power in watts (voltage × current) — shown on the power display
    power: float = 0.0
    # Engine temperature pass-through for the temperature panel
    temperature_engine: int = 0
    # Battery temperature pass-through for the temperature panel
    temperature_battery: int = 0
    # Chip temperature pass-through for the temperature panel
    temperature_chip: int = 0
    # Elapsed time since session start in milliseconds — displayed on the timer panel
    elapsed_time: int = 0
    # Estimated time remaining based on battery/fuel — shown alongside elapsed time
    remaining_time: int = 0
    # Heading/yaw angle pass-through for the compass widget
    heading: float = 0.0
    # Angular velocity pass-through for the gyro-rate display
    gyro_z_rate: float = 0.0
    # X-axis linear acceleration pass-through for the accel panel
    lin_accel_x: float = 0.0
    # Y-axis linear acceleration pass-through for the g-force display
    lin_accel_y: float = 0.0
    # Highest speed observed during the session — shown in the stats sidebar
    max_speed: float = 0.0
    # Average speed over the session — shown in the stats sidebar
    avg_speed: float = 0.0
    # Cumulative milliseconds the vehicle has been moving — used for efficiency calcs
    moving_time_ms: int = 0
    # Cumulative milliseconds the vehicle has been stationary — distinguishes idle from drive time
    stopped_time_ms: int = 0
    # Total energy consumed in kWh, accumulated by the energy tracker
    energy_kwh: float = 0.0
    # Rolling average lap time in milliseconds — computed by the lap timer
    avg_lap_time_ms: float = 0.0
    # Moving-window average acceleration for trend display
    acceleration_avg: float = 0.0
    # Moving-window minimum acceleration for peak/valley tracking
    acceleration_min: float = 0.0
    # Moving-window maximum acceleration for peak/valley tracking
    acceleration_max: float = 0.0
    # Moving-window average g-force for trend display
    gforce_avg: float = 0.0
    # Moving-window minimum g-force for peak/valley tracking
    gforce_min: float = 0.0
    # Moving-window maximum g-force for peak/valley tracking
    gforce_max: float = 0.0
    # Moving-window average packet delay for latency trend display
    delay_avg: float = 0.0
    # Moving-window minimum packet delay for latency-spike detection
    delay_min: float = 0.0
    # Moving-window maximum packet delay for latency-spike detection
    delay_max: float = 0.0
    # Moving-window average packet loss for loss-trend display
    packet_loss_avg: float = 0.0
    # Moving-window minimum packet loss for loss-trend display
    packet_loss_min: float = 0.0
    # Moving-window maximum packet loss for worst-case loss display
    packet_loss_max: float = 0.0
    # Moving-window average voltage for power-quality trend display
    voltage_avg: float = 0.0
    # Moving-window minimum voltage for brownout detection
    voltage_min: float = 0.0
    # Moving-window maximum voltage for overvoltage detection
    voltage_max: float = 0.0
    # Moving-window average current for current-draw trend display
    current_avg: float = 0.0
    # Moving-window minimum current for current-draw analysis
    current_min: float = 0.0
    # Moving-window maximum current for current-spike detection
    current_max: float = 0.0
    # Moving-window average power for power-trend display
    power_avg: float = 0.0
    # Moving-window minimum power for power-dip detection
    power_min: float = 0.0
    # Moving-window maximum power for peak-power display
    power_max: float = 0.0
    # Moving-window average velocity for speed-trend display
    velocity_avg: float = 0.0
    # Moving-window minimum velocity for speed-trend display
    velocity_min: float = 0.0
    # Moving-window maximum velocity for top-speed tracking
    velocity_max: float = 0.0
    # Moving-window average RPM for RPM-trend display
    rpm_avg: float = 0.0
    # Moving-window minimum RPM for RPM-trend display
    rpm_min: float = 0.0
    # Moving-window maximum RPM for RPM-trend display
    rpm_max: float = 0.0
    # Moving-window average battery temperature for thermal-trend display
    temp_battery_avg: float = 0.0
    # Moving-window minimum battery temperature for thermal-trend display
    temp_battery_min: float = 0.0
    # Moving-window maximum battery temperature for overheat detection
    temp_battery_max: float = 0.0
    # Moving-window average chip temperature for thermal-trend display
    temp_chip_avg: float = 0.0
    # Moving-window minimum chip temperature for thermal-trend display
    temp_chip_min: float = 0.0
    # Moving-window maximum chip temperature for overheat detection
    temp_chip_max: float = 0.0
    # Moving-window average engine temperature for thermal-trend display
    temp_engine_avg: float = 0.0
    # Moving-window minimum engine temperature for thermal-trend display
    temp_engine_min: float = 0.0
    # Moving-window maximum engine temperature for overheat detection
    temp_engine_max: float = 0.0
    # Mutable list of active error-code strings — populated each tick from TransmittedData.status
    list_with_errors: list = field(default_factory=list)

    # Reset every field back to its default — used to clear the HUD between sessions without creating a new instance
    def reset(self):
        # Iterate over all dataclass-declared fields so we don't miss new fields added later
        for f in self.__dataclass_fields__:
            # Grab the default value declared in the class definition
            default = self.__dataclass_fields__[f].default
            # If the default is a factory callable (like field(default_factory=list)), call it to produce a fresh value
            if callable(default):
                setattr(self, f, default())
            # Otherwise assign the literal default directly (int 0, float 0.0, bool False, etc.)
            else:
                setattr(self, f, default)

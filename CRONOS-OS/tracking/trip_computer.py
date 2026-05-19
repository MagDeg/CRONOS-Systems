"""Trip computer — tracks moving/stopped time, max speed, avg speed.

All values are published to DisplayData so they can be consumed by
the Trip popup and any other UI component.
"""

# DisplayData is the shared mutable data bus that TickLoop reads each frame
from data.displayed_data import DisplayData


class TripComputer:
    """Records trip-level statistics over a session.

    Attributes:
        moving_time: Accumulated seconds with velocity > 0.1 km/h.
        stopped_time: Accumulated seconds with velocity ≤ 0.1 km/h.
        max_speed: Highest velocity seen so far (km/h).
    """

    # Any speed at or below this threshold is treated as "stopped"
    MOVING_THRESHOLD: float = 0.1  # km/h

    def __init__(self) -> None:
        # No time accumulated yet at the start of a trip session
        self.moving_time: float = 0.0
        self.stopped_time: float = 0.0
        # Track the highest speed observed for the trip summary display
        self.max_speed: float = 0.0

    def tick(self, dt: float, velocity_kmh: float, display: DisplayData) -> None:
        """Update trip counters and write results to DisplayData.

        Args:
            dt: Time delta in seconds.
            velocity_kmh: Current vehicle speed in km/h.
            display: Mutable DisplayData instance to write into.
        """
        # Classify the current tick as moving or stopped based on the threshold
        if velocity_kmh > self.MOVING_THRESHOLD:
            # Vehicle is moving — accumulate moving time
            self.moving_time += dt
        else:
            # Vehicle is stationary — accumulate stopped time
            self.stopped_time += dt

        # Update the peak speed if current velocity exceeds the previous record
        if velocity_kmh > self.max_speed:
            self.max_speed = velocity_kmh

        # Publish max speed to the shared data bus for the UI to consume
        display.max_speed = self.max_speed
        # Convert moving time to milliseconds (DisplayData convention for the UI)
        display.moving_time_ms = int(self.moving_time * 1000)
        # Convert stopped time to milliseconds (DisplayData convention for the UI)
        display.stopped_time_ms = int(self.stopped_time * 1000)

        # Derive average speed from total distance divided by moving hours
        moving_hours = self.moving_time / 3600.0
        # Guard against division by zero when the vehicle hasn't moved yet
        display.avg_speed = display.distance / moving_hours if moving_hours > 0 else 0.0

    def reset(self) -> None:
        """Zero all trip counters."""
        # Reset all accumulators for a fresh trip session
        self.moving_time = 0.0
        self.stopped_time = 0.0
        self.max_speed = 0.0

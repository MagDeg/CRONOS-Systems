"""Lap timer — detects lap completions from estimated_rounds.

A lap is considered complete each time ``estimated_rounds`` passes an
integer boundary.  Individual lap durations are recorded and the
running average is written to DisplayData.
"""

# Wall-clock timestamps are needed to measure the duration of each lap
import time

# DisplayData is the shared mutable data bus that TickLoop reads each frame
from data.displayed_data import DisplayData


class LapTimer:
    """Detects lap completions and maintains average lap time.

    Attributes:
        completed_laps: Number of full laps detected.
        lap_times: Duration (seconds) of each completed lap.
        _lap_start: Timestamp when the current lap started.
    """

    def __init__(self) -> None:
        # No laps completed at the start of a session
        self.completed_laps: int = 0
        # Empty list of lap durations — populated as laps are completed
        self.lap_times: list[float] = []
        # Record the startup timestamp as the beginning of the first lap
        self._lap_start: float = time.time()

    def tick(self, estimated_rounds: float, display: DisplayData) -> None:
        """Check for lap boundary crossings and update avg_lap_time_ms.

        Args:
            estimated_rounds: Current lap count (may be fractional).
            display: Mutable DisplayData to write into.
        """
        # The integer part of estimated_rounds is the number of fully completed laps
        laps = int(estimated_rounds)
        # A new lap is complete when the integer part has increased since the last tick
        if laps > self.completed_laps:
            # Capture the timestamp of this lap-completion event
            now = time.time()
            # Duration of the just-completed lap = current time minus lap-start time
            self.lap_times.append(now - self._lap_start)
            # Update the completed-lap counter to match the new integer count
            self.completed_laps = laps
            # The next lap starts right now
            self._lap_start = now

        # Only publish an average if at least one lap has been completed
        if self.lap_times:
            # Average lap time in milliseconds (sum ÷ count × 1000)
            display.avg_lap_time_ms = (sum(self.lap_times) / len(self.lap_times)) * 1000
        else:
            # No laps yet — publish zero to avoid NaN appearing in the UI
            display.avg_lap_time_ms = 0.0

    def reset(self) -> None:
        """Reset lap counter, times, and start timestamp."""
        # Start fresh with zero completed laps
        self.completed_laps = 0
        # Clear all recorded lap durations
        self.lap_times.clear()
        # Reset the lap-start reference point to now
        self._lap_start = time.time()

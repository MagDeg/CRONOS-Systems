"""Dead-reckoning position tracker.

Integrates heading + velocity each tick to estimate (x, y) position
relative to the start point, and maintains a path history for the
route map popup.
"""

# Standard trig and time utilities needed for dead-reckoning math and timestamps
import math
import time

# DisplayData is the shared mutable data bus that TickLoop reads each frame
from data.displayed_data import DisplayData


class PositionTracker:
    """Estimates vehicle position via dead reckoning.

    Attributes:
        pos_x: Estimated X position (East, metres).
        pos_y: Estimated Y position (North, metres).
        path_points: List of (x, y) tuples forming the driven route.
    """

    def __init__(self) -> None:
        # Start at the origin; position is always relative to the starting point
        self.pos_x: float = 0.0
        self.pos_y: float = 0.0
        # Ring buffer of path points for the route-map popup in the UI
        self._path_points: list[tuple[float, float]] = []

    def tick(self, dt: float, velocity_kmh: float, heading_deg: float) -> None:
        """Integrate velocity and heading over dt to update position.

        Args:
            dt: Time delta in seconds.
            velocity_kmh: Vehicle speed in km/h.
            heading_deg: Heading in degrees (0 = North, clockwise).
        """
        # Skip integration when effectively stopped to avoid position drift noise
        if velocity_kmh < 0.1:
            return
        # Convert km/h to m/s so the position delta comes out in metres
        v_ms = velocity_kmh / 3.6
        # Convert heading from degrees to radians for use with sin/cos
        hd_rad = math.radians(heading_deg)
        # Eastward displacement = velocity × sin(heading) × time
        self.pos_x += v_ms * math.sin(hd_rad) * dt
        # Northward displacement = velocity × cos(heading) × time
        self.pos_y += v_ms * math.cos(hd_rad) * dt
        # Record every position update to reconstruct the driven route
        self._path_points.append((self.pos_x, self.pos_y))
        # Cap path history at 20 000 points to bound memory usage
        if len(self._path_points) > 20000:
            # Keep the most recent 15 000 points so the route tail stays visible
            self._path_points = self._path_points[-15000:]

    def get_path(self) -> list[tuple[float, float]]:
        """Return the accumulated path point list."""
        # Expose the path so the route-map popup can render it
        return self._path_points

    def reset(self) -> None:
        """Reset position and clear the path."""
        # Re-zero position for a fresh session or returning to the start line
        self.pos_x = 0.0
        self.pos_y = 0.0
        # Clear the accumulated route trace so it doesn't leak across sessions
        self._path_points.clear()

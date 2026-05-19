# tracking/__init__.py
# Exports all tracking classes used by TickLoop.
# Dead-reckoning position integration: heading + velocity → (x, y) coordinates
from .position_tracker import PositionTracker
# Trip-level statistics: moving/stopped time, max speed, average speed
from .trip_computer import TripComputer
# Error-code transition monitor — records non-zero status changes in a bounded queue
from .error_tracker import ErrorTracker
# Lap detection via integer-boundary crossings of the estimated_rounds field
from .lap_timer import LapTimer
# Energy consumption integration: power (W) × time → kilowatt-hours
from .energy_tracker import EnergyTracker

# Public API — lets consumers import all trackers from the tracking package
__all__ = ["PositionTracker", "TripComputer", "ErrorTracker", "LapTimer", "EnergyTracker"]

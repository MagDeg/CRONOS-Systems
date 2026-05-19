"""Error-queue tracker.

Monitors the transmitted ``status`` field and maintains a queue of
error entries.  When status changes to a non-zero code the error is
recorded; when it returns to zero (NO_ISSUES) the queue is cleared.
"""

# Use wall-clock time for error-entry timestamps so the UI can show "when"
import time

# ERROR_MAP translates numeric status codes into human-readable name/description pairs
from definitions.error_defs import ERROR_MAP

# Each error-queue entry: (timestamp, code, name, description)
ErrorEntry = tuple[float, int, str, str]


class ErrorTracker:
    """Tracks the error-code history from the transmitted status field.

    Attributes:
        queue: List of ErrorEntry tuples, newest first.
        _prev_code: The status code seen on the previous tick.
    """

    # Cap the error queue at 100 entries to prevent unbounded memory growth
    MAX_QUEUE: int = 100

    def __init__(self) -> None:
        # Empty queue at startup — no errors have been recorded yet
        self.queue: list[ErrorEntry] = []
        # No previous status means the very first tick is always treated as a transition
        self._prev_code: int = 0

    def tick(self, status: int) -> None:
        """Check for status transitions and update the queue.

        Args:
            status: The current transmitted status code.
        """
        # No change since the last tick — skip to avoid duplicate entries
        if status == self._prev_code:
            return

        # Update the previous-code tracker for comparison on the next tick
        self._prev_code = status

        # Status 0 means "NO_ISSUES" — clear the entire error queue
        if status == 0:
            self.queue.clear()
            return

        # Look up the human-readable name/description; fall back to UNKNOWN for unrecognised codes
        name, desc = ERROR_MAP.get(status, ("UNKNOWN", f"Unknown error code {status}"))
        # Prepend the new error so the most recent entry appears first in the UI
        self.queue.insert(0, (time.time(), status, name, desc))
        # Enforce the queue size limit by discarding the oldest entry
        if len(self.queue) > self.MAX_QUEUE:
            self.queue.pop()

    def reset(self) -> None:
        """Clear the error queue and reset the previous-code tracker."""
        # Wipe all recorded errors so a fresh session starts clean
        self.queue.clear()
        # Reset the previous-code state so the first tick after reset triggers a proper transition
        self._prev_code = 0

"""Rolling-window min/avg/max for named metrics.

Feeds numeric values for arbitrary key names into length-limited deques,
then exposes ``avg()``, ``min()``, ``max()`` over the most recent window
(default 50 samples).  Used by the stats panel to show per-lap and
per-session aggregates.
"""

# deque with maxlen gives O(1) append/popleft for rolling-window stats — auto-evicts oldest entries
from collections import deque

# Rolling-window statistics tracker: feed values and query avg/min/max over the last N samples
class StatsTracker:
    """Rolling-window statistics (avg/min/max) for arbitrary metric keys.

    Each key gets its own length-limited deque.  ``feed()`` appends a
    value; ``avg()``, ``min()``, and ``max()`` query over the current
    window.

    Attributes:
        _data: Dict mapping metric name → deque of recent float values.
        _maxlen: Maximum samples retained per key (default 50).
    """
    # Initialise with a max window size — each metric key gets its own bounded deque
    def __init__(self, maxlen=50):
        # Dict mapping metric name (str) → deque of recent float values
        self._data: dict[str, deque] = {}
        # Store max window size for all metric deques
        self._maxlen = maxlen

    # Append a new sample to the named metric's rolling window
    def feed(self, key: str, value: float):
        # Lazy-init: create the deque only on the first feed for this key
        if key not in self._data:
            # Bounded deque auto-evicts the oldest sample when it hits maxlen
            self._data[key] = deque(maxlen=self._maxlen)
        # Append the new sample — if at capacity, the oldest falls off automatically
        self._data[key].append(value)

    # Return the arithmetic mean of the window, or 0.0 if no samples yet
    def avg(self, key: str) -> float:
        # .get returns empty tuple for unseen keys, making sum/len safely produce 0.0
        d = self._data.get(key, [])
        # Guard against empty window to avoid ZeroDivisionError
        return sum(d) / len(d) if d else 0.0

    # Return the minimum value in the window, or 0.0 if no samples yet
    def min(self, key: str) -> float:
        # Empty deque raises ValueError on min() — guard with the `if d` check
        d = self._data.get(key, [])
        # Return 0.0 as the safe default when no samples have been fed for this key
        return min(d) if d else 0.0

    # Return the maximum value in the window, or 0.0 if no samples yet
    def max(self, key: str) -> float:
        # Same empty-guard pattern as min() to avoid ValueError on an empty deque
        d = self._data.get(key, [])
        # Return 0.0 as the safe default for unseen metrics
        return max(d) if d else 0.0

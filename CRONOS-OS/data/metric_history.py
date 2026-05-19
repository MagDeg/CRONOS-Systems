"""Ring-buffer storage for time-series metric data.

This module provides MetricHistory — a deque-backed store that keeps up
to ``maxlen`` samples per named metric.  Intended for plotting the last
N seconds of telemetry on the graph panel.

.. py:data:: history
   Module-level singleton instance (``maxlen=200``) used by the GUI.
"""

# Use deque for O(1) appends and automatic eviction of old samples when the buffer is full
from collections import deque


class MetricHistory:
    """Ring-buffer that stores time-stamped samples for named metrics.

    Each ``feed()`` call appends a timestamp to a shared deque and pushes
    the value for every key into per-metric deques.  ``get()`` returns
    aligned timestamp and data lists suitable for plotting.

    Attributes:
        _maxlen: Maximum number of samples retained per metric.
        _timestamps: Deque of float timestamps in insertion order.
        _data: Mapping of metric name → deque of float values.
    """
    # Store the max sample count so we can pass it to new per-metric deques when they are created lazily
    def __init__(self, maxlen=200):
        self._maxlen = maxlen
        # Shared timestamp deque — one entry per feed call, in chronological order
        self._timestamps: deque[float] = deque(maxlen=maxlen)
        # Dict of metric-name → deque, so callers can push/pull data for any named metric independently
        self._data: dict[str, deque[float]] = {}

    # Accept a single timestamp plus a dict of metric values so the caller can push many metrics at once
    def feed(self, timestamp: float, values: dict[str, float]):
        # Append the timestamp first so the timestamp deque length stays in sync with every metric deque
        self._timestamps.append(timestamp)
        # Walk every provided key-value pair so all metrics are recorded from the same tick
        for key, val in values.items():
            # Create a new deque for this metric the first time we see its key (lazy initialisation)
            if key not in self._data:
                self._data[key] = deque(maxlen=self._maxlen)
            # Append the float value so it lines up positionally with the shared timestamp deque
            self._data[key].append(float(val))

    # Return aligned timestamp and data lists so the caller can plot them directly without re-aligning
    def get(self, keys: list[str]):
        return list(self._timestamps), {
            k: list(self._data[k]) for k in keys if k in self._data
        }

    # Wipe all stored data so the caller can reset the graph without discarding the MetricHistory object
    def clear(self):
        self._timestamps.clear()
        self._data.clear()


# Module-level singleton used by every graph panel — 200 samples covers ~40 seconds at 200 ms ticks
history = MetricHistory()

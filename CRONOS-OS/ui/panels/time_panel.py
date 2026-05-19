"""Countdown / elapsed-time panel with current time display.

Widgets:
    TimePanel: Shows current time, elapsed time, remaining time, and average lap time.
"""

# Import base widget classes for composing the time display panel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
# Import Qt enums and timer for alignment and the 1-second clock update timer
from PySide6.QtCore import Qt, QTimer
# Import datetime to get the current wall-clock time for display
from datetime import datetime


class TimePanel(QWidget):
    """Panel showing current time, elapsed/remaining time, and average lap time."""

    # Build the time panel with four labeled time displays and a 1-second clock timer
    def __init__(self, index=0, title="Countdown", accent_color="#00aaff", parent=None):
        # Initialize QWidget
        super().__init__(parent)
        # Store the grid index for identification
        self._index = index

        # Main vertical layout for the panel
        layout = QVBoxLayout(self)
        # Horizontal padding with moderate vertical padding
        layout.setContentsMargins(8, 6, 8, 6)
        # Tight spacing between stacked time blocks
        layout.setSpacing(4)

        # Panel header identifying this section
        header = QLabel(title)
        # Shared panel-title styling
        header.setObjectName("PanelTitle")
        # Center the header
        header.setAlignment(Qt.AlignCenter)
        # Add the header at the top
        layout.addWidget(header)

        # Factory that builds a labeled time-display block (label above a time value)
        def _block(label_id, lbl):
            # Container widget for the labeled time block
            w = QWidget()
            # Vertical layout stacks the label above the time value
            l = QVBoxLayout(w)
            # Compact margins for a dense display
            l.setContentsMargins(4, 2, 4, 2)
            # Add the descriptive label (e.g. "Current Time") centered
            l.addWidget(QLabel(label_id, objectName="MetricLabel", alignment=Qt.AlignCenter))
            # Style the time value label with the large time-specific CSS class
            lbl.setObjectName("TimeValue")
            # Center the time text
            lbl.setAlignment(Qt.AlignCenter)
            # Add the time value label below the description
            l.addWidget(lbl)
            # Return the assembled block
            return w

        # Create the four time-value labels with initial placeholder text
        self._current = QLabel("-")
        self._elapsed = QLabel("-")
        self._remaining = QLabel("-")
        self._avg_lap = QLabel("-")

        # Factory that creates a thin horizontal separator frame
        def _sep():
            s = QFrame()
            s.setObjectName("ValueSeparator")
            return s

        # Add each labeled time block with stretch=1 for even vertical distribution
        layout.addWidget(_block("Current Time", self._current), 1)
        # Separate current time from elapsed time
        layout.addWidget(_sep())
        # Add elapsed time block
        layout.addWidget(_block("Elapsed Time", self._elapsed), 1)
        # Separate elapsed time from remaining time
        layout.addWidget(_sep())
        # Add remaining time block
        layout.addWidget(_block("Remaining Time", self._remaining), 1)
        # Separate remaining time from avg lap time
        layout.addWidget(_sep())
        # Add average lap time block
        layout.addWidget(_block("Avg Lap Time", self._avg_lap), 1)

        # Create a 1-second timer that updates the "Current Time" label with the actual clock
        self._time_timer = QTimer(self)
        # Connect each tick to the _update_current_time handler
        self._time_timer.timeout.connect(self._update_current_time)
        # Fire every 1000ms (1 second)
        self._time_timer.start(1000)
        # Immediately populate the current-time label without waiting for the first tick
        self._update_current_time()

        # Finalize the layout
        self.setLayout(layout)

    # Set the current-time label to the wall-clock time in HH:MM:SS format
    def _update_current_time(self):
        self._current.setText(datetime.now().strftime("%H:%M:%S"))

    # Convert milliseconds to a human-readable H:MM:SS or M:SS string
    def _fmt(self, ms: int) -> str:
        """Format milliseconds to H:MM:SS or M:SS."""
        # Return "0:00" for negative or zero values
        if ms < 0:
            return "0:00"
        # Convert milliseconds to whole seconds (rounded)
        s = int(round(ms / 1000))
        # Break seconds into hours and remainder
        h, r = divmod(s, 3600)
        # Break remainder into minutes and seconds
        m, sec = divmod(r, 60)
        # Show hours only when elapsed time exceeds 60 minutes
        return f"{h:d}:{m:02d}:{sec:02d}" if h > 0 else f"{m:d}:{sec:02d}"

    # Called every tick to refresh elapsed, remaining, and avg lap time from fresh telemetry
    def update_from_data(self, d):
        """Update elapsed, remaining, and avg lap time from a DisplayData object."""
        # Format and display elapsed time
        self._elapsed.setText(self._fmt(d.elapsed_time))
        # Format and display remaining time
        self._remaining.setText(self._fmt(d.remaining_time))
        # Format and display average lap time; show "-" when no lap data is available
        self._avg_lap.setText(self._fmt(int(d.avg_lap_time_ms)) if d.avg_lap_time_ms > 0 else "-")

    # Manually set all three time display strings (bypasses the data-object pipeline)
    def update_time(self, current: str, elapsed: str, remaining: str):
        """Manually set the three time display strings."""
        self._current.setText(current)
        self._elapsed.setText(elapsed)
        self._remaining.setText(remaining)

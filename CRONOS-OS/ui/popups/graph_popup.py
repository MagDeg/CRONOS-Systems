"""Full-size line-graph popup for multi-key metric history.

Widgets:
    LineGraphWidget: QPainter-drawn line chart with axes, grid lines, and per-series labels.
        Feeds from data.metric_history.history.
"""

# Import QWidget as the base widget class for the custom-painted line graph
from PySide6.QtWidgets import QWidget
# Import Qt enums for alignment constants used in text rendering
from PySide6.QtCore import Qt
# Import QPainter for custom 2D drawing, QPen/QColor for line styling, QFont for text
from PySide6.QtGui import QPainter, QPen, QColor, QFont

# Import the shared ring-buffer history object that provides timestamped series data
from data.metric_history import history

# Color palette cycled through for each data series — high-contrast colors for readability
_LINE_COLORS = ["#00d4ff", "#00ffa6", "#ff7f50", "#ffb432", "#ff5050", "#a0e0ff"]

class LineGraphWidget(QWidget):
    """QPainter-drawn multi-series line chart with axes, grid, and per-key color legend."""

    def __init__(self, keys, x_label="Data Point", y_label="Value", parent=None):
        # Init QWidget so this custom-painted widget can be embedded in layouts
        super().__init__(parent)
        # Store the list of metric keys to fetch from history and render as series
        self._keys = keys
        # X-axis label drawn vertically along the bottom (e.g. "Data Point")
        self._x_label = x_label
        # Y-axis label drawn rotated 90° along the left side (e.g. "Value")
        self._y_label = y_label
        # Assign each key a color from the palette, cycling when more keys than colors exist
        self._colors = {k: _LINE_COLORS[i % len(_LINE_COLORS)] for i, k in enumerate(keys)}
        # Minimum size ensures the graph doesn't collapse and stays legible
        self.setMinimumSize(400, 240)

    def paintEvent(self, event):
        """Paint the full line chart: background, grid, Y-axis labels, series lines, and key labels."""
        p = QPainter(self)
        # Anti-aliasing smooths the diagonal lines for a polished look
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        # Margin widths: left (for Y-axis labels), right, top, bottom (for X-axis labels)
        ml, mr, mt, mb = 64, 40, 30, 52
        pw, ph = w - ml - mr, h - mt - mb
        # Dimensions of the actual plot area after subtracting margins

        # Fill the entire widget with the dark background
        p.fillRect(0, 0, w, h, QColor("#050814"))

        # Fetch all timestamps and series data from the ring buffer for the configured keys
        timestamps, series = history.get(self._keys)
        # If no data or fewer than 2 timestamps, show a placeholder message and exit early
        if not timestamps or len(timestamps) < 2:
            p.setPen(QColor("#a0e0ff"))
            p.setFont(QFont("Segoe UI", 12))
            p.drawText(self.rect(), Qt.AlignCenter, "Collecting data...")
            p.end()
            return

        # Collect all values across all series to compute the global Y-axis min and max
        all_vals = [v for vals in series.values() for v in vals]
        if not all_vals:
            p.end()
            return
        vmin, vmax = min(all_vals), max(all_vals)
        # Prevent division by zero in the normalization math when all values are identical
        if vmax == vmin:
            vmax = vmin + 1
        val_range = vmax - vmin

        # Draw 5 horizontal grid lines across the plot area at 1/4-spaced intervals
        y_axis = QColor("rgba(160, 224, 255, 0.3)")
        p.setPen(QPen(y_axis, 1))
        for i in range(5):
            y = mt + ph * i / 4
            p.drawLine(int(ml), int(y), int(w - mr), int(y))

        # Draw Y-axis numeric labels aligned to the right of each grid line
        p.setPen(QColor("#a0e0ff"))
        p.setFont(QFont("Segoe UI", 9))
        for i in range(5):
            y = mt + ph * i / 4
            val = vmax - val_range * i / 4
            p.drawText(2, int(y - 6), ml - 8, 12, Qt.AlignRight | Qt.AlignVCenter, f"{val:.1f}")

        # Draw 5 short tick marks along the X-axis at 1/4 intervals
        n = len(timestamps)
        p.setPen(QPen(QColor("rgba(160, 224, 255, 0.3)"), 1))
        for i in range(5):
            x = ml + pw * i / 4
            p.drawLine(int(x), int(h - mb), int(x), int(h - mb + 4))
        # Draw X-axis index labels below each tick mark
        p.setPen(QColor("#a0e0ff"))
        p.setFont(QFont("Segoe UI", 9))
        for i in range(5):
            x = ml + pw * i / 4
            idx = int(n * i / 4)
            p.drawText(int(x - 24), h - mb + 6, 48, 12, Qt.AlignCenter, str(idx))

        # Render one line series per configured key
        for key in self._keys:
            vals = series.get(key)
            if not vals or len(vals) < 2:
                continue
            color = QColor(self._colors[key])
            p.setPen(QPen(color, 2))
            # If this series has fewer points than the full timestamp range, offset it so it
            # right-aligns with the latest timestamp
            offset = n - len(vals)
            # Project each data point from data-space to pixel-space
            path = [(ml + (i + offset) / (n - 1) * pw,
                     mt + ph - (v - vmin) / val_range * ph)
                    for i, v in enumerate(vals)]

            # Draw the connecting line segments for this series
            for i in range(1, len(path)):
                p.drawLine(int(path[i - 1][0]), int(path[i - 1][1]),
                           int(path[i][0]), int(path[i][1]))

            # Draw the series label (the metric key name) next to the last data point
            label_x = int(path[-1][0]) + 4
            label_y = int(path[-1][1]) + 4
            p.setFont(QFont("Segoe UI", 9, QFont.Bold))
            p.setPen(color)
            p.drawText(label_x, label_y - 2, 80, 14, Qt.AlignLeft | Qt.AlignVCenter, key)

        # Draw the Y-axis label rotated 90 degrees counter-clockwise on the left margin
        p.save()
        p.translate(12, mt + ph / 2)
        p.rotate(-90)
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(-ph / 2, 0, ph, 18, Qt.AlignCenter, self._y_label)
        p.restore()
        p.end()

"""QPainter-drawn 2D route map with grid, path, start/current markers, and heading line.

Widgets:
    RouteWidget: Top-down route plot showing traversed points, current position,
        a heading indicator, compass rose, and scale bar.
"""

# Math for trigonometric heading-line calculations and log10-based grid/scale step sizing
import math

# QWidget as the base class for this custom-painted widget
from PySide6.QtWidgets import QWidget
# Core Qt types: alignment flags, rectangle for text, and 2D point
from PySide6.QtCore import Qt, QRectF, QPointF
# Painting primitives: painter, color, pen, and font
from PySide6.QtGui import QPainter, QColor, QPen, QFont


class RouteWidget(QWidget):
    """QPainter-drawn 2D route map with grid, path trace, start/current markers, heading, and scale."""

    def __init__(self, parent=None):
        # Initialize the QWidget base to hook into Qt's parent-child and paint system
        super().__init__(parent)
        # List of (x, y) tuples representing the traversed path in world coordinates
        self._points = []
        # Current vehicle X position in world coordinates
        self._cur_x = 0.0
        # Current vehicle Y position in world coordinates
        self._cur_y = 0.0
        # Current heading in degrees; used to draw the heading line from the current position
        self._heading = 0.0
        # Minimum size so the map doesn't become unusably small when the window is shrunk
        self.setMinimumSize(400, 300)

    def update_path(self, points, cur_x, cur_y, heading):
        """Set the route path, current position, and heading; trigger repaint."""
        # Replace the full point list so the trace reflects the latest telemetry history
        self._points = points
        self._cur_x = cur_x
        self._cur_y = cur_y
        self._heading = heading
        # Request a full repaint so the map updates immediately with the new data
        self.update()

    def _to_screen(self, world_x, world_y, cx, cy, scale):
        # Convert world coordinates to screen coordinates: world Y is inverted so +Y goes up on screen
        return QPointF(cx + world_x * scale, cy - world_y * scale)

    def paintEvent(self, event):
        """Paint the route: background, grid, path line, start dot, current-position dot, heading line,
        compass rose, and scale bar."""
        # Create a QPainter for this widget; all drawing targets the widget's pixel surface
        p = QPainter(self)
        # Anti-aliasing for smooth lines, circles, and text
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        # Fill the entire widget with the dark navy HUD background
        p.fillRect(0, 0, w, h, QColor(5, 10, 30))

        # If no route points have been set yet, show a placeholder instead of an empty map
        if not self._points:
            p.setPen(QColor(100, 100, 120))
            p.setFont(QFont("Segoe UI", 12))
            p.drawText(self.rect(), Qt.AlignCenter, "No route data")
            return

        # Collect all X coordinates (path points + current) to compute the view bounds
        all_x = [pt[0] for pt in self._points] + [self._cur_x]
        # Collect all Y coordinates similarly
        all_y = [pt[1] for pt in self._points] + [self._cur_y]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        # Width of the data range in world units; clamp to 1.0 to avoid division by zero when all X are identical
        rx = max(max_x - min_x, 1.0)
        # Height of the data range similarly clamped
        ry = max(max_y - min_y, 1.0)

        # 50px margin on all sides so grid labels and the scale bar aren't clipped
        margin = 50
        plot_w = w - 2 * margin
        plot_h = h - 2 * margin
        # Scale factor to fit the data into the plot area while preserving aspect ratio
        scale = min(plot_w / rx, plot_h / ry)

        # Center of the widget in screen coordinates
        cx = w / 2.0
        cy = h / 2.0
        # Center of the data in world coordinates
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0

        # Local helper to convert a world point to a screen point, centered and scaled
        def to_screen(wx, wy):
            return QPointF(cx + (wx - center_x) * scale, cy - (wy - center_y) * scale)

        # Compute a "nice" grid step using powers of 10 so grid lines fall on round numbers
        grid_step = 10 ** math.floor(math.log10(max(rx, ry) / 4))
        # Safety check: if the range is extremely small, fall back to step 1
        if grid_step <= 0:
            grid_step = 1
        # Very faint cyan pen for the grid so it provides reference without distracting from the path
        p.setPen(QPen(QColor(0, 191, 255, 18), 1))
        # Start vertical grid lines at the first grid_step-aligned X left of center
        gx = math.floor((min_x - center_x) / grid_step) * grid_step + center_x
        # Draw vertical grid lines from left to right across the data range
        while gx <= max_x:
            sx = cx + (gx - center_x) * scale
            p.drawLine(QPointF(sx, margin), QPointF(sx, h - margin))
            gx += grid_step
        # Start horizontal grid lines at the first grid_step-aligned Y below center
        gy = math.floor((min_y - center_y) / grid_step) * grid_step + center_y
        # Draw horizontal grid lines from bottom to top across the data range
        while gy <= max_y:
            sy = cy - (gy - center_y) * scale
            p.drawLine(QPointF(margin, sy), QPointF(w - margin, sy))
            gy += grid_step

        # Only draw the path line if there are at least 2 points (a line needs two endpoints)
        if len(self._points) > 1:
            pen = QPen(QColor(0, 191, 255), 2)
            # Round joins so path corners don't have sharp spikes
            pen.setJoinStyle(Qt.RoundJoin)
            # Round caps so line ends are smooth
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            # Start from the first point and connect successive points with line segments
            prev = to_screen(self._points[0][0], self._points[0][1])
            for pt in self._points[1:]:
                cur = to_screen(pt[0], pt[1])
                p.drawLine(prev, cur)
                prev = cur

        # Draw the start point as a green dot
        start = to_screen(self._points[0][0], self._points[0][1])
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 255, 100, 200))
        p.drawEllipse(start, 5, 5)

        # Draw the current position as a larger red dot with a light red outline so it stands out from the path
        cur_pt = to_screen(self._cur_x, self._cur_y)
        p.setBrush(QColor(255, 80, 80, 220))
        p.setPen(QPen(QColor(255, 180, 180), 1))
        p.drawEllipse(cur_pt, 6, 6)

        # Convert heading to radians for trigonometric projection of the heading line
        hd_rad = math.radians(self._heading)
        # Yellow dashed line showing the direction the vehicle is heading
        p.setPen(QPen(QColor(255, 200, 100, 120), 1, Qt.DashLine))
        hd_end = QPointF(
            cur_pt.x() + 25 * math.sin(hd_rad),
            cur_pt.y() - 25 * math.cos(hd_rad),
        )
        # Draw the short heading line emanating from the current position dot
        p.drawLine(cur_pt, hd_end)

        # Draw a small compass rose in the top-left margin area
        p.setPen(QPen(QColor(0, 191, 255, 150), 1))
        p.setFont(QFont("Segoe UI", 9))
        # Small circle representing the compass body
        p.drawEllipse(QPointF(margin + 15, margin + 15), 6, 6)
        # "N" label to the right of the compass circle indicating the north direction
        p.drawText(QRectF(margin + 25, margin + 7, 40, 16), Qt.AlignLeft, "N")

        # Compute a "nice" scale bar length using powers of 10, roughly 1/3 of the data range
        slen = 10 ** math.floor(math.log10(max(rx, ry) / 3))
        # Only draw the scale bar if the calculated length is positive
        if slen > 0:
            # Convert the scale bar length from world units to screen pixels
            sx_px = slen * scale
            # Bottom-left corner of the scale bar in screen coordinates
            bx = margin + 10
            by = h - margin - 10
            p.setPen(QPen(QColor(160, 224, 255), 1))
            # Horizontal line for the scale bar
            p.drawLine(QPointF(bx, by), QPointF(bx + sx_px, by))
            # Left vertical tick
            p.drawLine(QPointF(bx, by - 3), QPointF(bx, by + 3))
            # Right vertical tick
            p.drawLine(QPointF(bx + sx_px, by - 3), QPointF(bx + sx_px, by + 3))
            # Label showing the scale length in meters or kilometers
            label = f"{slen:.0f}m" if slen < 1000 else f"{slen/1000:.1f}km"
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRectF(bx, by + 4, sx_px, 14), Qt.AlignCenter, label)

        # Summary info line at the top of the widget
        p.setPen(QColor(160, 224, 255))
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(QRectF(margin, 4, w - 2 * margin, 20), Qt.AlignLeft,
                   f"Points: {len(self._points)}  |  Heading: {self._heading:.0f}°")

"""QPainter-drawn heading compass with cardinal labels and gyro Z readout.

Widgets:
    HeadingWidget: Circular compass rose with needle, N/E/S/W markers, heading
        text overlay, and gyro Z rate display beneath the compass.
"""

# Math for trigonometric calculations when drawing tick marks, the needle, and cardinal positions
import math

# QWidget as the base class for this custom-painted widget
from PySide6.QtWidgets import QWidget
# Core Qt types: alignment flags, rectangle geometry, and 2D point
from PySide6.QtCore import Qt, QRectF, QPointF
# Painting primitives: the painter itself, path shapes, colors, pens, and fonts
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen, QFont


class HeadingWidget(QWidget):
    """QPainter-drawn circular compass with heading needle, cardinal labels, and gyro Z readout."""

    def __init__(self, parent=None):
        # Initialize the QWidget base to participate in Qt's widget hierarchy
        super().__init__(parent)
        # Default heading: north (0 degrees); updated from telemetry each tick
        self._heading = 0.0
        # Default gyro Z rate; updated from telemetry each tick
        self._gyro_z = 0.0
        # Enforce a minimum size so the compass circle and gyro label aren't squished at small window sizes
        self.setMinimumSize(380, 380)

    def update_data(self, heading: float, gyro_z: float):
        """Set new heading and gyro Z rate values; trigger repaint."""
        # Normalize heading to [0, 360) so the needle always points in the correct angular range
        self._heading = heading % 360.0
        # Store the raw gyro Z rate (°/s) for display beneath the compass
        self._gyro_z = gyro_z
        # Schedule a repaint so paintEvent redraws the compass with the new values
        self.update()

    def paintEvent(self, event):
        """Paint the compass rose, tick marks, cardinal text, heading needle, and gyro label."""
        # Create a QPainter tied to this widget; all drawing operations target the widget's surface
        p = QPainter(self)
        # Enable anti-aliasing so circles, lines, and text edges render smoothly
        p.setRenderHint(QPainter.Antialiasing)

        # Center X coordinate of the widget
        cx = self.width() / 2.0
        # Center Y coordinate of the widget
        cy = self.height() / 2.0
        # Reserve 50px at the bottom for the gyro Z text label
        label_bottom = 50
        # Compute the compass circle radius: smallest half-dimension minus bottom label room and a 12px outer padding
        r = min(cx, cy - label_bottom) - 12

        # Dim cyan pen for the compass outer ring
        p.setPen(QPen(QColor(0, 191, 255, 60), 1))
        # Dark navy brush for the compass face background
        p.setBrush(QColor(5, 10, 30))
        # Draw the filled compass circle centered on (cx, cy) with the computed radius
        p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Save the current transform so we can translate to center and later restore
        p.save()
        # Translate origin to the center of the compass for relative drawing of ticks and needle
        p.translate(cx, cy)

        # Use the inner radius (2px inset from the outer ring) for tick mark endpoints
        inner_r = r - 2
        # Step through every 10 degrees to draw tick marks around the compass
        for angle in range(0, 360, 10):
            # Every 30° is a major tick (bolder, longer); 10° and 20° between majors are minor ticks
            major = angle % 30 == 0
            # Convert compass angle to radians, subtracting 90 so 0° points up (north) instead of right
            a_rad = math.radians(angle - 90)
            if major:
                # Bright cyan for major ticks so the 30° intervals stand out
                p.setPen(QPen(QColor(0, 191, 255), 2))
                # Major tick starts 18px inward from the inner radius
                x1 = (inner_r - 18) * math.cos(a_rad)
                y1 = (inner_r - 18) * math.sin(a_rad)
                # Major tick extends to the inner radius edge
                x2 = inner_r * math.cos(a_rad)
                y2 = inner_r * math.sin(a_rad)
            else:
                # Dimmer, thinner pen for minor ticks so they don't visually overwhelm major ticks
                p.setPen(QPen(QColor(0, 191, 255, 70), 1))
                # Minor tick starts only 10px inward, making it shorter than major ticks
                x1 = (inner_r - 10) * math.cos(a_rad)
                y1 = (inner_r - 10) * math.sin(a_rad)
                x2 = inner_r * math.cos(a_rad)
                y2 = inner_r * math.sin(a_rad)
            # Draw a single tick mark line from the inner start point to the outer endpoint
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Grab the current font from the painter so we can modify and reuse it
        font = p.font()
        # Bold for cardinal labels so N/E/S/W are legible at a glance
        font.setBold(True)
        # 16pt is large enough to read quickly while driving
        font.setPointSize(16)
        # Apply the modified font to the painter
        p.setFont(font)
        # White text for maximum contrast against the dark compass background
        p.setPen(QColor(255, 255, 255))
        # Define the four cardinal directions with their compass degrees
        cardinals = [("N", 0), ("E", 90), ("S", 180), ("W", 270)]
        for text, deg in cardinals:
            # Convert degrees to radians, offset by -90 so 0° (north) is at the top
            a = math.radians(deg - 90)
            # Place the label 30px inward from the inner radius ring
            lx = (inner_r - 30) * math.cos(a)
            ly = (inner_r - 30) * math.sin(a)
            # Draw centered text in a 36x36 bounding box so each cardinal letter is nicely centered on its position
            p.drawText(QRectF(lx - 18, ly - 18, 36, 36), Qt.AlignCenter, text)

        # Convert the current heading to radians, offset by -90 so the needle points up at 0°
        hr = math.radians(self._heading - 90)
        # Needle tip is 26px from the inner radius, leaving room for the cardinal labels beneath
        tip_len = inner_r - 26
        # No outline on the needle for a clean triangular shape
        p.setPen(Qt.NoPen)
        # Red fill so the heading needle is immediately visible against the dark/cyan compass
        p.setBrush(QColor(255, 80, 80))
        # Build a triangular needle path pointing in the heading direction
        path = QPainterPath()
        # Needle tip at the heading angle
        path.moveTo(tip_len * math.cos(hr), tip_len * math.sin(hr))
        # Left base of the triangle, offset 1.4 radians from the heading for a ~80° point
        path.lineTo(-10 * math.cos(hr - 1.4), -10 * math.sin(hr - 1.4))
        # Right base of the triangle, symmetric to the left side
        path.lineTo(-10 * math.cos(hr + 1.4), -10 * math.sin(hr + 1.4))
        # Close the triangle path back to the tip
        path.closeSubpath()
        # Draw the filled triangular needle
        p.drawPath(path)

        # Dark brush for the center hub circle so it blends with the compass face
        p.setBrush(QColor(5, 10, 30))
        # Semi-transparent cyan outline for the hub ring
        p.setPen(QPen(QColor(0, 191, 255, 150), 2))
        # 44px diameter hub circle centered at the origin (cx, cy after translation)
        p.drawEllipse(QRectF(-22, -22, 44, 44))

        # Switch back to normal weight for the heading number readout inside the hub
        font.setBold(False)
        # Smaller font to fit the heading value inside the hub
        font.setPointSize(11)
        # Apply the modified font
        p.setFont(font)
        # Soft cyan text color for the numeric readout
        p.setPen(QColor(160, 224, 255))
        # Draw the heading as a whole number with a degree symbol, centered in the hub
        p.drawText(QRectF(-30, -14, 60, 28), Qt.AlignCenter, f"{self._heading:.0f}°")

        # Restore the painter's transform so subsequent drawing uses widget coordinates again
        p.restore()

        # 13pt font for the gyro label below the compass
        font.setPointSize(13)
        p.setFont(font)
        p.setPen(QColor(160, 224, 255))
        # Draw gyro Z rate centered below the compass circle with two decimal precision
        p.drawText(QRectF(0, cy + r + 20, self.width(), 28), Qt.AlignCenter, f"Gyro Z: {self._gyro_z:.2f} °/s")

    def sizeHint(self):
        # Report the minimum size as the preferred size so layout managers don't shrink the compass below usability
        return self.minimumSize()

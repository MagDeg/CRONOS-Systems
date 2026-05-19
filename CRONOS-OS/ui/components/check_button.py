"""Custom toggle-switch widget styled with QPainter.

Widgets:
    ToggleSwitch: Labeled on/off toggle resembling a mobile-style switch.
    _SwitchCheckbox: Internal QPainter-drawn checkbox that paints the rounded track and knob.
"""

# QWidget for the base class, QHBoxLayout to arrange the toggle and label horizontally, QLabel for the text label
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
# Qt for alignment flags and cursor shape constants
from PySide6.QtCore import Qt


class ToggleSwitch(QWidget):
    """Labeled on/off toggle switch with custom QPainter-drawn checkbox."""

    def __init__(self, label="", initial=False, parent=None):
        # Initialize the QWidget so this toggle is properly managed by Qt's widget tree
        super().__init__(parent)
        # Store the initial on/off state so the checkbox can be drawn correctly from the start
        self._checked = initial
        # Create a horizontal layout: checkbox on the left, label on the right
        layout = QHBoxLayout(self)
        # Tight margins so the switch and label sit close together without excess padding
        layout.setContentsMargins(4, 4, 4, 4)

        # Create the custom-painted checkbox (the visual toggle track + knob)
        self._checkbox = _SwitchCheckbox(self)
        # Sync the checkbox's internal state with the initial value so the painted knob position is correct
        self._checkbox.setChecked(initial)

        # Create a QLabel for the descriptive text next to the toggle
        self._label = QLabel(label)
        # Assign a named stylesheet selector so the QSS in styles.qss can style this label independently
        self._label.setObjectName("SwitchLabel")

        # Add the checkbox and label to the layout in order
        layout.addWidget(self._checkbox)
        layout.addWidget(self._label)
        # Push everything to the left by adding a stretch after the label
        layout.addStretch()
        # Attach the layout to this widget
        self.setLayout(layout)

    def is_checked(self) -> bool:
        """Return the current toggle state."""
        # Delegate to the checkbox so the toggle state is always read from the single source of truth
        return self._checkbox.isChecked()

    def set_checked(self, checked: bool):
        # Forward to the checkbox so the painted knob position updates and a repaint is triggered
        self._checkbox.setChecked(checked)


class _SwitchCheckbox(QWidget):
    """QPainter-drawn toggle checkbox (rounded track + sliding knob)."""

    def __init__(self, parent=None):
        # Initialize QWidget so painting and mouse events work correctly
        super().__init__(parent)
        # Start in the unchecked (off) state; callers must call setChecked if they want a different default
        self._checked = False
        # Fixed 44×24 pixel size so the track proportions resemble a standard mobile toggle switch
        self.setFixedSize(44, 24)
        # Show a hand cursor on hover so users know this element is clickable
        self.setCursor(Qt.PointingHandCursor)

    def isChecked(self):
        """Return whether the switch is in the on position."""
        # Return the internal boolean so external code (like ToggleSwitch) can read the state
        return self._checked

    def setChecked(self, checked):
        """Set checked state and trigger repaint."""
        # Update the internal state
        self._checked = checked
        # Force a repaint so the knob slides to the new on/off position visually
        self.update()

    def mouseReleaseEvent(self, event):
        """Toggle state on click."""
        # Flip the checked state whenever the user clicks and releases on this widget
        self._checked = not self._checked
        # Repaint immediately so the knob animates to the new position
        self.update()
        # Call the base implementation so any other mouse-release handlers (e.g. parent) are notified
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """Paint the rounded track and circular knob using current state color."""
        # Import late so this file's top-level imports stay minimal; QPainter is only needed inside paint
        from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
        # Create a painter tied to this widget's drawing surface
        p = QPainter(self)
        # Anti-aliasing so the rounded rect and circle edges are smooth
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        # Green track when checked (on), gray track when unchecked (off) — matches platform conventions
        bg_color = QColor("#34c759") if self._checked else QColor("#555")
        # No outline on the track for a clean modern look
        p.setPen(Qt.NoPen)
        p.setBrush(bg_color)
        # Draw the rounded rectangular track; the corner radius equals half the height for a pill shape
        p.drawRoundedRect(0, 0, w, h, h / 2, h / 2)

        # Knob X position: right side (w - h + 2) when checked, left side (2) when unchecked — 2px inset on each side
        knob_x = w - h + 2 if self._checked else 2
        # White knob for contrast against both green and gray backgrounds
        p.setBrush(QBrush(QColor("#ffffff")))
        # Draw the circular knob (h - 4 = 20px diameter, inset 2px from the track edges)
        p.drawEllipse(int(knob_x), 2, h - 4, h - 4)

        # Finalize painting; pairs with the QPainter constructor
        p.end()

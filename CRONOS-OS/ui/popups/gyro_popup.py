"""Full-screen popup dialog for heading and gyroscope display.

Widgets:
    GyroPopup: Dialog embedding a HeadingWidget compass alongside a close button.
"""

# Import QDialog as the popup base, QVBoxLayout/QHBoxLayout for vertical/horizontal stacking,
# QPushButton for the close action, QLabel for the title text, QFrame for separator lines
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
# Import the Qt enum namespace so we can reference alignment constants like AlignCenter
from PySide6.QtCore import Qt

# Import the custom HeadingWidget that renders a QPainter compass rose from heading/gyro data
from ui.components.heading_widget import HeadingWidget


class GyroPopup(QDialog):
    """Dialog embedding a HeadingWidget compass with close button."""

    def __init__(self, parent=None):
        # Initialize the QDialog base so this window behaves as a proper popup dialog
        super().__init__(parent)
        # Set a descriptive title so the OS task bar identifies this as the heading/gyro view
        self.setWindowTitle("Heading · Gyroscope")
        # Fix the dialog size so the compass always has a predictable, usable canvas
        self.setFixedSize(540, 640)
        # Assign a Qt object name so the QSS stylesheet can target this popup with #GyroPopup rules
        self.setObjectName("GyroPopup")

        # Create a vertical layout as the root; it stacks children top-to-bottom
        layout = QVBoxLayout(self)
        # Add margins so content doesn't bleed into the dark window border
        layout.setContentsMargins(16, 16, 16, 16)
        # Use tight spacing between stacked elements for a dense HUD feel
        layout.setSpacing(10)

        # Title label explaining what this popup shows — user needs a clear header
        header = QLabel("Heading · Gyroscope")
        # Tag it with PanelTitle so the global stylesheet applies the correct font/color
        header.setObjectName("PanelTitle")
        # Center the title horizontally above the compass widget
        header.setAlignment(Qt.AlignCenter)
        # Insert the title at the top of the vertical stack
        layout.addWidget(header)

        # A thin horizontal rule to visually separate the title from the content area
        sep = QFrame()
        # QSS object name so the stylesheet paints it as a dim cyan separator line
        sep.setObjectName("ValueSeparator")
        layout.addWidget(sep)

        # Create the compass widget — the main visual component of this popup
        self._compass = HeadingWidget()
        # Add the compass with stretch factor 1 so it fills all available vertical space
        layout.addWidget(self._compass, 1)

        sep2 = QFrame()
        sep2.setObjectName("ValueSeparator")
        layout.addWidget(sep2)

        # Horizontal layout to center the close button via left/right stretches
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        # Standard close affordance so the user can dismiss the popup
        close_btn = QPushButton("Close")
        # Tag it with SettingsButton so the stylesheet gives it the dark panel-button look
        close_btn.setObjectName("SettingsButton")
        # Fixed width prevents the button from stretching across the whole dialog
        close_btn.setFixedWidth(100)
        # Connect clicked → accept() so the dialog closes with QDialog::Accepted
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        btn_row.addStretch()
        # Attach the horizontal button row to the bottom of the vertical layout
        layout.addLayout(btn_row)

        # Inline stylesheet guarantees the dark background even if the QSS file fails to load
        self.setStyleSheet("""
            #GyroPopup {
                background-color: #050814;
            }
        """)

    def update_from_data(self, display) -> None:
        """Forward heading and gyro Z rate from a DisplayData object to the compass widget."""
        # Push the latest heading and gyro Z-axis rate into the compass so it redraws the needle
        self._compass.update_data(display.heading, display.gyro_z_rate)

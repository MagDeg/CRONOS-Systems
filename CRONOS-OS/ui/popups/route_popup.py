"""Full-screen popup dialog for the driven route map.

Widgets:
    RoutePopup: Dialog embedding a RouteWidget with close button.
"""

# Import QDialog as the popup base, QVBoxLayout/QHBoxLayout for layout composition,
# QPushButton for dismissal, QLabel for the header, QFrame for visual separators
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
# Import Qt namespace for alignment constants (AlignCenter) used by the header label
from PySide6.QtCore import Qt

# Import the custom RouteWidget that paints a 2D GPS breadcrumb trail on a QPainter canvas
from ui.components.route_widget import RouteWidget


class RoutePopup(QDialog):
    """Dialog embedding a RouteWidget map with close button."""

    def __init__(self, parent=None):
        # Initialize the QDialog base so this behaves as a standard modal popup
        super().__init__(parent)
        # Set the window title so the OS identifies this as the route display
        self.setWindowTitle("Driven Route")
        # Set a minimum size so the route map never gets squashed below usable dimensions
        self.setMinimumSize(560, 480)
        # Default resize gives a comfortable starting canvas for the breadcrumb trail
        self.resize(640, 520)
        # Object name for QSS targetability via #RoutePopup selectors
        self.setObjectName("RoutePopup")

        # Root vertical layout stacks title, separator, route widget, separator, close button
        layout = QVBoxLayout(self)
        # Tight margins so the dark background fills the window while content stays inset
        layout.setContentsMargins(12, 12, 12, 12)
        # Compact spacing between stacked elements for a dense telemetry-HUD look
        layout.setSpacing(8)

        # Title label to identify the view — user must know they're looking at a route map
        header = QLabel("Driven Route")
        # Tag for QSS styling from the global PanelTitle rule
        header.setObjectName("PanelTitle")
        # Center the title above the route widget
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Separator QFrame acts as a visual horizontal rule between title and map
        sep = QFrame()
        sep.setObjectName("ValueSeparator")
        layout.addWidget(sep)

        # The RouteWidget is the core visual — it draws the GPS path and current vehicle position
        self._route = RouteWidget()
        # Stretch factor 1 lets the route widget consume all remaining vertical space
        layout.addWidget(self._route, 1)

        sep2 = QFrame()
        sep2.setObjectName("ValueSeparator")
        layout.addWidget(sep2)

        # Horizontal layout with side stretches to center the close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        # Close button so the user can dismiss the popup
        close_btn = QPushButton("Close")
        # QSS tag for consistent dark panel-button styling
        close_btn.setObjectName("SettingsButton")
        # Cap the button width so it doesn't span the full dialog width
        close_btn.setFixedWidth(100)
        # Clicking Close calls accept() to close the dialog with Accepted result
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Inline background-color guarantees the dark space theme even if QSS stylesheet is missing
        self.setStyleSheet("""
            #RoutePopup {
                background-color: #050814;
            }
        """)

    def update_path(self, points, cur_x, cur_y, heading):
        """Forward route data to the embedded RouteWidget."""
        # Push the latest set of GPS breadcrumbs and current position+heading into the widget for repaint
        self._route.update_path(points, cur_x, cur_y, heading)

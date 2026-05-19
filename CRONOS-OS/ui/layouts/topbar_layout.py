"""Top bar layout for C.R.O.N.O.S. OS.

Provides the heading indicator bar with popup-launching buttons
(HDG, MAP, STAT, TRIP, TRND) and update methods that forward
telemetry data to each open popup.
"""

# Import QWidget as the base, QHBoxLayout for horizontal button layout, QLabel for the title, QPushButton for popup launchers
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
# Import Qt enums for cursor styling and alignment constants
from PySide6.QtCore import Qt

# Import all popup widgets that are launched by the top bar buttons
from ui.popups.gyro_popup import GyroPopup
from ui.popups.route_popup import RoutePopup
from ui.popups.module_status_popup import ModuleStatusPopup
from ui.popups.trip_popup import TripPopup
from ui.popups.trends_popup import TrendsPopup


class TopBar(QWidget):
    """Fixed-height top bar with system title and popup-launching buttons."""

    def __init__(self, parent=None):
        """Build the top bar: title label + HDG / MAP / STAT / TRIP / TRND buttons.

        Each button is wired to a private ``_open_*`` slot that creates
        and shows the corresponding popup widget on first click.
        """
        # Initialise the QWidget base so this bar can be embedded in the main window layout
        super().__init__(parent)
        # Tag the widget for QSS styling — the stylesheet targets #TopBar to set the bar's background and border
        self.setObjectName("TopBar")
        # Fix the height to 60px so the bar is always the same size regardless of content
        self.setFixedHeight(60)
        # Lazy-init references for popup instances; None means "not yet created" or "closed"
        self._gyro_popup = None
        self._route_popup = None
        self._status_popup = None
        self._trip_popup = None
        self._trends_popup = None

        # Use a horizontal layout so the title sits on the left and buttons cluster on the right
        layout = QHBoxLayout(self)
        # Add horizontal margins so the content doesn't touch the window edges
        layout.setContentsMargins(20, 0, 20, 0)

        # Create the system title label that identifies the application in the top bar
        title = QLabel("C.R.O.N.O.S. | OS")
        # Tag the title so QSS can apply the distinctive cyan HUD font style
        title.setObjectName("TopBarTitle")
        # Add the title to the left side of the layout
        layout.addWidget(title)
        # Push all remaining space after the title, forcing buttons to the right
        layout.addStretch()

        # Shared button style configuration dict so all five buttons look identical
        BTN = {"name": "HeadingButton", "fixed": (40, 32), "cursor": Qt.PointingHandCursor}

        # Build the HDG button that opens the gyro/heading attitude popup
        self._hdg_btn = QPushButton("HDG")
        self._hdg_btn.setObjectName(BTN["name"])
        self._hdg_btn.setFixedSize(*BTN["fixed"])
        self._hdg_btn.setCursor(BTN["cursor"])
        self._hdg_btn.clicked.connect(self._open_gyro)
        layout.addWidget(self._hdg_btn)

        # Build the MAP button that opens the route/navigation popup
        self._map_btn = QPushButton("MAP")
        self._map_btn.setObjectName(BTN["name"])
        self._map_btn.setFixedSize(*BTN["fixed"])
        self._map_btn.setCursor(BTN["cursor"])
        self._map_btn.clicked.connect(self._open_route)
        layout.addWidget(self._map_btn)

        # Build the STAT button that opens the module status / error-list popup
        self._stat_btn = QPushButton("STAT")
        self._stat_btn.setObjectName(BTN["name"])
        self._stat_btn.setFixedSize(*BTN["fixed"])
        self._stat_btn.setCursor(BTN["cursor"])
        self._stat_btn.clicked.connect(self._open_status)
        layout.addWidget(self._stat_btn)

        # Build the TRIP button that opens the trip / odometer details popup
        self._trip_btn = QPushButton("TRIP")
        self._trip_btn.setObjectName(BTN["name"])
        self._trip_btn.setFixedSize(*BTN["fixed"])
        self._trip_btn.setCursor(BTN["cursor"])
        self._trip_btn.clicked.connect(self._open_trip)
        layout.addWidget(self._trip_btn)

        # Build the TRND button that opens the historical trends popup
        self._trnd_btn = QPushButton("TRND")
        self._trnd_btn.setObjectName(BTN["name"])
        self._trnd_btn.setFixedSize(*BTN["fixed"])
        self._trnd_btn.setCursor(BTN["cursor"])
        self._trnd_btn.clicked.connect(self._open_trends)
        layout.addWidget(self._trnd_btn)

        # Attach the completed layout to this widget so children render
        self.setLayout(layout)

    def _open_gyro(self):
        """Show the GyroPopup (heading/sensor attitude display)."""
        # Create a new popup only if one doesn't exist or was closed, to avoid duplicate windows
        if self._gyro_popup is None or not self._gyro_popup.isVisible():
            self._gyro_popup = GyroPopup(self.window())
            self._gyro_popup.show()

    def _open_route(self):
        """Show the RoutePopup (navigation map)."""
        if self._route_popup is None or not self._route_popup.isVisible():
            self._route_popup = RoutePopup(self.window())
            self._route_popup.show()

    def _open_status(self):
        """Show the ModuleStatusPopup (error/warning list)."""
        if self._status_popup is None or not self._status_popup.isVisible():
            self._status_popup = ModuleStatusPopup(self.window())
            self._status_popup.show()

    def _open_trip(self):
        """Show the TripPopup (trip/odometer details)."""
        if self._trip_popup is None or not self._trip_popup.isVisible():
            self._trip_popup = TripPopup(self.window())
            self._trip_popup.show()

    def _open_trends(self):
        """Show the TrendsPopup (historical trend charts)."""
        if self._trends_popup is None or not self._trends_popup.isVisible():
            self._trends_popup = TrendsPopup(self.window())
            self._trends_popup.show()

    def update_gyro(self, display) -> None:
        """Forward *display* data to the gyro popup if it is visible."""
        # Push updated telemetry to the gyro popup only when it's open, to avoid unnecessary work
        if self._gyro_popup and self._gyro_popup.isVisible():
            self._gyro_popup.update_from_data(display)

    def update_route(self, points, cur_x, cur_y, heading) -> None:
        """Forward path and position data to the route popup if visible."""
        if self._route_popup and self._route_popup.isVisible():
            self._route_popup.update_path(points, cur_x, cur_y, heading)

    def update_module_status(self, error_queue) -> None:
        """Forward error-queue entries to the module-status popup if visible."""
        if self._status_popup and self._status_popup.isVisible():
            self._status_popup.update_errors(error_queue)

    def update_trip(self, display) -> None:
        """Forward *display* data to the trip popup if it is visible."""
        if self._trip_popup and self._trip_popup.isVisible():
            self._trip_popup.update_from_data(display)

    def update_trends(self) -> None:
        """Trigger a trends refresh on the trends popup if it is visible."""
        if self._trends_popup and self._trends_popup.isVisible():
            self._trends_popup.update_trends()


def get_topbar_layout():
    """Construct and return a fresh ``TopBar`` instance."""
    return TopBar()

"""Top-level application window for C.R.O.N.O.S. OS.

Orchestrates the top bar and main content view.  The single
``update_all_widgets`` method is called by the application timer to
push ``DisplayData`` through the entire widget tree.
"""

# Import Qt's main window frame, base widget, and vertical layout so we can build the top-level window chrome
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
# Import icon support so the window gets a recognizable taskbar/titlebar icon
from PySide6.QtGui import QIcon

# Import the top bar that holds heading indicator and popup-launching buttons
from ui.layouts.topbar_layout import TopBar
# Import the main content area that splits stats grid and sidebar horizontally
from ui.layouts.main_view_layout import MainView


class MainWindow(QMainWindow):
    """Application main window holding the top bar and main content view."""

    def __init__(self, parent=None):
        """Build the window: top bar + main view (stats + sidebar) stacked vertically."""
        # Delegate to QMainWindow so we get native window chrome, event loop integration, and central-widget support
        super().__init__(parent)
        # Set a human-readable title so the window manager and taskbar identify the application
        self.setWindowTitle("C.R.O.N.O.S. OS")
        # Load the SVG icon asset so the window decoration shows the project logo
        self.setWindowIcon(QIcon("assets/icon.svg"))
        # Assign an object name so the QSS stylesheet can style this window via #MainWindow
        self.setObjectName("MainWindow")

        # Create a plain QWidget as the invisible root container that fills the window's client area
        central = QWidget()
        # Tag the container for QSS targeting so the app background styling applies correctly
        central.setObjectName("AppContainer")
        # Use a vertical box layout so children stack top-to-bottom without any side-by-side arrangement
        layout = QVBoxLayout(central)
        # Eliminate margins so the top bar and main content extend fully to the window edges
        layout.setContentsMargins(0, 0, 0, 0)
        # Remove spacing between stacked children so they appear as a seamless single surface
        layout.setSpacing(0)

        # Construct the top bar widget that contains the system title and HDG/MAP/STAT/TRIP/TRND buttons
        self._topbar = TopBar()
        # Construct the main view widget that holds the stats card grid and right sidebar
        self._main_view = MainView()

        # Insert the top bar first so it renders at the top of the window (no stretch, natural height)
        layout.addWidget(self._topbar)
        # Insert the main view with stretch factor 1 so it consumes all remaining vertical space
        layout.addWidget(self._main_view, 1)

        # Register the container as QMainWindow's central widget, making it the root of the widget tree
        self.setCentralWidget(central)

    def update_all_widgets(self, display_data):
        """Propagate *display_data* (a ``DisplayData``) to all child widgets."""
        # Forward the computed display data to MainView, which fans it out to every panel widget
        self._main_view.update_all(display_data)


def get_main_layout():
    """Construct and return a fresh ``MainWindow`` instance."""
    return MainWindow()

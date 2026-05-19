"""Main content view for C.R.O.N.O.S. OS.

Horizontally splits the area between the stats/graph centre panel
and the right sidebar (settings + command console).
"""

# Import QWidget as the base class and QHBoxLayout for horizontal side-by-side arrangement
from PySide6.QtWidgets import QWidget, QHBoxLayout

# Import the right sidebar that contains settings, log tabs, and the command console
from ui.layouts.sidebar_layout import RightSidebar
# Import the central stats panel that holds the clickable card grid and graph detail view
from ui.layouts.stats_layout import StatsLayout


class MainView(QWidget):
    """Horizontal split: stats grid (3) | right sidebar (1)."""

    def __init__(self, parent=None):
        """Lay out the stats panel and right sidebar side-by-side.

        The stats area receives stretch factor 3, the sidebar factor 1.
        """
        # Initialise the QWidget base so this view can be embedded in the main window layout
        super().__init__(parent)
        # Tag the widget for QSS styling so the content background and borders are applied consistently
        self.setObjectName("ContentContainer")

        # Use a horizontal box layout to place stats and sidebar next to each other
        layout = QHBoxLayout(self)
        # Add small horizontal margins so the content doesn't touch the window edge directly
        layout.setContentsMargins(8, 0, 8, 0)
        # Set spacing between the stats area and sidebar for visual breathing room
        layout.setSpacing(12)

        # Build the central stats panel with the 2x3 card grid and graph detail page
        self._stats = StatsLayout()
        # Build the right sidebar containing settings, multi-tab logs, and command input
        self._right_sidebar = RightSidebar()

        # Add the stats panel with stretch factor 3 so it gets most of the horizontal space
        layout.addWidget(self._stats, 3)
        # Add the sidebar with stretch factor 1 so it gets a narrower but consistent width
        layout.addWidget(self._right_sidebar, 1)
        # Attach the layout to this widget so children are rendered and resized automatically
        self.setLayout(layout)

    def update_all(self, d):
        """Forward *d* to the central stats panel for widget updates."""
        # Delegate to the stats layout, which fans out the DisplayData to each card panel
        self._stats.update_all(d)


def get_main_view_layout():
    """Construct and return a fresh ``MainView`` instance."""
    return MainView()

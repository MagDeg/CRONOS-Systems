"""Stats / graph layout for C.R.O.N.O.S. OS.

Displays a 2×3 grid of clickable metric cards.  Clicking a card
switches a ``QStackedWidget`` to a dedicated graph page with live
``LineGraphWidget`` instances.  A back button returns to the grid.
"""

# Import Qt widgets for building the card grid, stacked pages, scrollable graph area, and back button
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QStackedWidget, QPushButton, QLabel, QScrollArea
# Import Qt core enums for cursor styling and QTimer for periodic graph refresh
from PySide6.QtCore import Qt, QTimer

# Import the six dashboard panel widgets that populate the clickable cards
from ui.panels.speed_drive_panel import CompactSpeedDriveGauges
from ui.panels.electric_values import CombinedPowerPanel
from ui.panels.temperature_panel import CombinedTempPanel
from ui.panels.accel_gforce_panel import AccelGForceDistance
from ui.panels.connection_panel import CombinedNetworkPanel
from ui.panels.time_panel import TimePanel
# Import the line-graph widget used in the detail page when a card is clicked
from ui.popups.graph_popup import LineGraphWidget


# Semi-transparent dark card style with a subtle cyan border for the dark-HUD theme
_CARD_STYLE = """
QFrame#PanelCard {
    background-color: rgba(15, 25, 45, 0.55);
    border: 1px solid rgba(0, 191, 255, 0.15);
    border-radius: 10px;
}
QFrame#PanelCard:hover {
    border: 1px solid rgba(0, 191, 255, 0.4);
}
"""

# Back-button style: translucent white text on a faint background, cyan border on hover
_BACK_BTN_STYLE = """
QPushButton#BackBtn {
    background-color: rgba(255, 255, 255, 0.08);
    color: #a0e0ff;
    border: 1px solid rgba(0, 191, 255, 0.2);
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 12px;
}
QPushButton#BackBtn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(0, 191, 255, 0.4);
}
"""

# Map each card title to the metric keys it exposes so the graph page knows which data series to plot
_PANEL_METRICS = {
    "Driving Data": ["velocity", "rpm"],
    "Electrical": ["voltage", "voltage_battery", "battery_pct", "current", "power"],
    "Temperatures": ["temperature_battery", "temperature_chip", "temperature_engine"],
    "Acceleration \u00b7 G\u2011Force": ["acceleration", "g_force"],
    "Network": ["packet_loss", "delay"],
    "Countdown": ["elapsed_time", "remaining_time"],
}


class _ClickableCard(QFrame):
    """A styled card that emits a callback on click.

    Wraps an arbitrary widget (gauge panel, etc.) and fires
    ``on_click(title, metric_keys)`` when the card is pressed.
    """

    def __init__(self, content, title, metric_keys, on_click, parent=None):
        """Wrap *content* in a clickable card with hover styling.

        Args:
            content: The inner widget to display inside the card.
            title: Human-readable card title.
            metric_keys: List of metric key strings for graph construction.
            on_click: Callable ``(title, metric_keys)`` invoked on press.
        """
        # Initialise the QFrame base so we get a rectangular visual container
        super().__init__(parent)
        # Store the title so mousePressEvent can pass it to the callback
        self._title = title
        # Store the metric keys so the graph page knows which lines to plot
        self._metric_keys = metric_keys
        # Store the callback so clicking this card triggers the graph-page transition
        self._on_click = on_click
        # Assign the object name so QSS targets this frame with the card style
        self.setObjectName("PanelCard")
        # Apply the dark semi-transparent card style with cyan border
        self.setStyleSheet(_CARD_STYLE)
        # Change the cursor to a pointing hand to signal interactivity
        self.setCursor(Qt.PointingHandCursor)
        # Use a vertical layout so the embedded content fills the card from edge to edge
        l = QVBoxLayout(self)
        # Remove card internal margins so the content widget touches the card border
        l.setContentsMargins(0, 0, 0, 0)
        # Insert the content widget (gauge panel) into the card layout
        l.addWidget(content)

    def mousePressEvent(self, event):
        """Forward the card title and metric keys to the registered callback."""
        # Ignore the event object — just fire the callback so the stack flips to the graph page
        self._on_click(self._title, self._metric_keys)


class StatsLayout(QWidget):
    """Central stats area with a grid of clickable cards and a graph detail view.

    Uses a ``QStackedWidget`` to flip between:
        - Index 0: 2×3 grid of ``_ClickableCard`` panels.
        - Index 1: A dynamically built graph page with ``LineGraphWidget``s.
    """

    def __init__(self, parent=None):
        """Build the stacked layout: grid page + timer for graph refresh."""
        # Initialise the QWidget base so this layout can be embedded in the main view
        super().__init__(parent)
        # Tag the widget for QSS targeting, matching the #Main style from the stylesheet
        self.setObjectName("Main")

        # Root layout for this widget — holds the QStackedWidget exclusively
        layout = QVBoxLayout(self)
        # Remove margins so the stacked widget fills the entire available area
        layout.setContentsMargins(0, 0, 0, 0)

        # Create the stacked widget that flips between the card grid (index 0) and graph page (index 1)
        self._stack = QStackedWidget()
        # Add the stack to the layout so it occupies all space
        layout.addWidget(self._stack)

        # Build the 2x3 card grid page and add it at stack index 0
        self._stats_grid = self._build_grid()
        self._stack.addWidget(self._stats_grid)

        # Create a timer that drives periodic repaint of graph widgets while the graph page is active
        self._graph_timer = QTimer(self)
        # Use PreciseTimer so graph refresh is not throttled by Qt's coarse timer coalescing
        self._graph_timer.setTimerType(Qt.PreciseTimer)
        # Connect the timer's timeout to _refresh_graph, which repaints every LineGraphWidget
        self._graph_timer.timeout.connect(self._refresh_graph)

    def _build_grid(self):
        """Construct the 2×3 card grid page (stack index 0)."""
        # Create a plain widget to serve as the page container
        page = QWidget()
        # Tag the page so QSS can style the grid background
        page.setObjectName("Main")
        # Vertical layout that stacks the two rows of cards
        layout = QVBoxLayout(page)
        # Add margins so the cards have breathing room from the page edges
        layout.setContentsMargins(8, 8, 8, 8)
        # Set vertical spacing between the two rows
        layout.setSpacing(12)

        # Factory closure that wraps a panel widget in a _ClickableCard wired to _show_graph
        def _card(w, title):
            return _ClickableCard(w, title, _PANEL_METRICS[title],
                                  self._show_graph)

        # Build the six dashboard panel widgets that appear inside the clickable cards
        sd = CompactSpeedDriveGauges(index=3)
        pw = CombinedPowerPanel(index=0)
        tp = CombinedTempPanel(index=1)

        ac = AccelGForceDistance(index=4)
        nw = CombinedNetworkPanel(index=5)
        tm = TimePanel(index=0)

        # Keep references to all panel widgets so update_all can push data to them
        self._panel_widgets = [sd, pw, tp, ac, nw, tm]

        # Top row: Driving Data, Electrical, Temperatures
        row1 = QWidget()
        r1 = QHBoxLayout(row1)
        r1.setContentsMargins(0, 0, 0, 0)
        r1.setSpacing(12)
        r1.addWidget(_card(sd, "Driving Data"), 1)
        r1.addWidget(_card(pw, "Electrical"), 1)
        r1.addWidget(_card(tp, "Temperatures"), 1)

        # Bottom row: Acceleration/G-Force, Network, Countdown
        row2 = QWidget()
        r2 = QHBoxLayout(row2)
        r2.setContentsMargins(0, 0, 0, 0)
        r2.setSpacing(12)
        r2.addWidget(_card(ac, "Acceleration \u00b7 G\u2011Force"), 1)
        r2.addWidget(_card(nw, "Network"), 1)
        r2.addWidget(_card(tm, "Countdown"), 1)

        # Add both rows to the page layout, each with equal stretch to split vertical space evenly
        layout.addWidget(row1, 1)
        layout.addWidget(row2, 1)
        return page

    def _build_graph_page(self, title, keys):
        """Build a detail page (stack index 1) with a back button and live graphs.

        One ``LineGraphWidget`` per metric key is created inside a scroll area.
        A 500 ms timer drives ``_refresh_graph`` while this page is active.

        Args:
            title: Heading text displayed at the top of the page.
            keys: Metric keys to plot (e.g. ``["velocity", "rpm"]``).
        """
        # Create a page container widget that will be inserted at stack index 1
        page = QWidget()
        # Tag the page so QSS applies the same background style as the grid page
        page.setObjectName("Main")
        # Vertical layout: back-button row on top, scrollable graphs below
        layout = QVBoxLayout(page)
        # Add margins to prevent content from touching the page edges
        layout.setContentsMargins(8, 8, 8, 8)
        # Tight vertical spacing to conserve screen real estate for graphs
        layout.setSpacing(6)

        # Horizontal row holding the back button and the page title
        top = QHBoxLayout()
        back = QPushButton("\u2190 Back")
        back.setObjectName("BackBtn")
        back.setStyleSheet(_BACK_BTN_STYLE)
        back.clicked.connect(self._back_to_grid)
        top.addWidget(back)

        heading = QLabel(title)
        heading.setObjectName("PanelTitle")
        heading.setAlignment(Qt.AlignCenter)
        top.addWidget(heading, 1)
        layout.addLayout(top)

        # Scroll area so many graph widgets don't overflow the screen
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # Inner container that holds the vertical column of graph widgets
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        # Build one LineGraphWidget per metric key so each data series gets its own chart
        self._graph_widgets = []
        for key in keys:
            gw = LineGraphWidget([key], x_label="", y_label=key)
            # Set a minimum height so each graph is readable even with many series
            gw.setMinimumHeight(180)
            self._graph_widgets.append(gw)
            cl.addWidget(gw)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # Start the 500ms timer to continuously repaint the graphs while this page is shown
        self._graph_timer.start(500)
        return page

    def _show_graph(self, title, keys):
        """Remove any existing graph page and build a fresh one at stack index 1."""
        # Destroy any previously built graph page to free memory and avoid stale widgets
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            w.deleteLater()

        # Stop the existing timer before building a new page to avoid redundant repaints
        self._graph_timer.stop()
        page = self._build_graph_page(title, keys)
        self._stack.addWidget(page)
        # Switch to the graph page (index 1) so the user sees the charts
        self._stack.setCurrentIndex(1)

    def _refresh_graph(self):
        """Repaint every graph widget on the current graph page."""
        # Trigger a repaint on each graph widget so they fetch new metric history and redraw
        for gw in self._graph_widgets:
            gw.update()

    def _back_to_grid(self):
        """Stop the graph timer and return to the card grid (stack index 0)."""
        # Stop the timer so graph widgets stop refreshing when they're not visible
        self._graph_timer.stop()
        # Clear the graph widget list so stale references don't accumulate
        self._graph_widgets = []
        # Switch back to the card grid (index 0) so the user sees the overview
        self._stack.setCurrentIndex(0)

    def update_all(self, d):
        """Push *d* (a ``DisplayData`` instance) to every panel widget on the grid."""
        # Fan out the data to each panel widget so gauges and values update every tick
        for w in self._panel_widgets:
            w.update_from_data(d)


def get_stats_layout():
    """Construct and return a fresh ``StatsLayout`` instance."""
    return StatsLayout()

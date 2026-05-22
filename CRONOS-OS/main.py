"""CRONOS OS — Native Linux desktop telemetry dashboard.

Builds a PySide6 ``QApplication``, loads the Qt stylesheet, creates the
data pipeline (``TransmittedData`` → ``DisplayDataCalculator`` →
``DisplayData``), and starts a 500 ms ``QTimer`` that drives the update
loop.  ``discover_serial_port()`` auto-detects the first available serial
port; if found a background ``SerialReader`` thread is started, otherwise
``DemoDataGenerator`` supplies synthetic data.
"""

# Import sys for access to command-line arguments and the exit() function
import sys

# Import QApplication — the core class needed to instantiate any PySide6 GUI
from PySide6.QtWidgets import QApplication
# Import QTimer to drive the periodic 500 ms dashboard update loop
from PySide6.QtCore import QTimer
# Import QFont for setting a default application font and QIcon for the window icon
from PySide6.QtGui import QFont, QIcon

# Import the thread-safe data model that holds raw telemetry fields received over serial
from data.received_data import TransmittedData
# Import the computed display model that stores values ready for widget rendering
from data.displayed_data import DisplayData
# Import the transformer that converts raw TransmittedData into DisplayData
from core.display_data_calculator import DisplayDataCalculator
# Import demo data generation utilities and the serial-port discovery helper
from core.demo_generator import DemoDataGenerator, discover_serial_port
# Import the background thread that reads telemetry from the serial port
from core.serial_background_reading import SerialReader
# Import the singleton CSV logger for recording telemetry data to disk
from core.csv_logger import csv_logger
# Import the main application window that composes all dashboard panels
from ui.layouts.main_layout import MainWindow
# Import the coordinator that runs all per-tick logic every 500 ms
from tick_loop import TickLoop


# Define the application entry point
def main():
    # Create the QApplication; sys.argv passes CLI arguments to Qt for things like -style
    app = QApplication(sys.argv)
    # Set the application name for window-manager identification and the WM_CLASS property
    app.setApplicationName("CRONOS OS")
    # Force the Fusion Qt style for a consistent cross-platform dark-theme look
    app.setStyle("Fusion")
    # Load the SVG icon so it appears in the title bar, taskbar, and window switcher
    app.setWindowIcon(QIcon("assets/icon.svg"))

    # Try to load the custom QSS stylesheet; if missing, fall back to default Fusion styling
    try:
        # Open the stylesheet file that defines the dark HUD theme with cyan accents
        with open("assets/styles.qss") as f:
            # Apply the entire stylesheet globally to style all Qt widgets
            app.setStyleSheet(f.read())
    # Gracefully handle a missing stylesheet so the application still starts
    except FileNotFoundError:
        # Silently continue — the default Fusion look is acceptable as a fallback
        pass
    # Set the default application font for a clean, modern look across all widgets
    app.setFont(QFont("Segoe UI", 10))

    # Create the shared raw-data container that the serial-reader background thread writes into
    transmitted = TransmittedData()
    # Create the computed display-data container that every widget reads for rendering
    display = DisplayData()
    # Create the calculator that transforms raw telemetry fields into display-ready values
    calculator = DisplayDataCalculator(display, transmitted)

    # Instantiate the main dashboard window with all panels and sidebars laid out
    window = MainWindow()
    # Make the window visible on screen
    window.show()
    # Set a default window size large enough to fit all dashboard panels without scrolling
    window.resize(1400, 900)

    # Create the demo data generator that produces synthetic telemetry when no serial hardware is available
    demo = DemoDataGenerator(transmitted)

    # Grab a reference to the right sidebar for wiring up the serial reader and settings state
    sidebar = window._main_view._right_sidebar
    # Initialize the sidebar's reader reference to None until we confirm a serial port exists
    sidebar._reader = None
    # Give the sidebar access to the raw TransmittedData for the debug display panel
    sidebar._td = transmitted
    # Auto-discover the first available serial port on this system
    serial_port = discover_serial_port()
    # Check whether a serial device was found
    if serial_port is not None:
        # Wrap serial setup in try/except in case the device exists but fails to open
        try:
            # Create the serial reader thread configured for 115200 baud
            reader = SerialReader(serial_port, transmitted, 115200)
            # Start the background thread that continuously reads telemetry packets
            reader.start()
            # Store the reader reference on the sidebar so tick logic can check connection state
            sidebar._reader = reader
            # Open a new CSV log file to record all incoming telemetry for post-session analysis
            csv_logger.open()
            # Show the CSV log filename in the settings panel so the operator knows data is being saved
            sidebar._settings.set_csv_label(csv_logger.basename)
            # Display the serial port path in the settings panel for operator awareness
            sidebar._settings.set_port_label(serial_port)
        # Catch any serial-setup failure (permissions, wrong device, etc.) without crashing the app
        except Exception:
            # Silently fall back to demo mode — the reader stays None and the app runs on synthetic data
            pass

    # Create the tick-loop coordinator that orchestrates all per-tick data processing and widget updates
    loop = TickLoop(window, transmitted, display, calculator, demo)

    # Create a QTimer to fire periodic ticks that drive the entire dashboard update cycle
    timer = QTimer()
    # Connect the timer's timeout signal to the tick method so it executes on every interval
    timer.timeout.connect(loop.tick)
    # Start the timer at 500 ms, giving approximately 2 dashboard updates per second
    timer.start(500)

    # Enter the Qt event loop and exit with the application's return code when the window is closed
    sys.exit(app.exec())


# Guard so main() only runs when this file is executed directly, never when imported as a module
if __name__ == "__main__":
    # Call the entry-point function to start the full application
    main()

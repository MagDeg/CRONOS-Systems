"""Reads semicolon-delimited telemetry from a serial port in a daemon thread.

Parses 15-field packets, writes parsed values into a shared
:class:`~data_structs.received_data.TransmittedData` (under its internal
lock), and forwards the raw line to :data:`~csv_logger.csv_logger`.

Threading notes
---------------
The read loop runs on a separate daemon thread.  All writes to
``transmitted_data`` are protected by ``transmitted_data.lock``.
The ``running`` flag is a plain ``bool`` — safe for this single-writer,
single-reader pattern because the flag is only toggled from the main
thread and read from the background thread.
"""

# threading.Thread needed for the background daemon that reads serial without blocking the GUI
import threading
# time.sleep for read-loop backpressure and time.time for last_data_time watchdog timestamps
import time
# queue.Queue for thread-safe raw data transfer from the serial thread to the GUI thread
import queue
# pyserial library for cross-platform serial-port communication
import serial
# Structured logging so serial errors go to the app's log system instead of stdout
import logging

# Shared telemetry struct that the background thread populates under a lock
from data.received_data import TransmittedData
# Module-level CSV logger singleton — the background thread writes raw lines to it
from core.csv_logger import csv_logger

# Per-module logger so log records include "serial_background_reading" as their source
logger = logging.getLogger(__name__)

# Background serial reader: runs a daemon thread that polls a serial port and parses 15-field packets
class SerialReader:
    """Reads 15-field semicolon-delimited telemetry from a serial port.

    Runs a daemon thread that calls ``on_data()`` for every complete
    line received.  Parsed values are written into the shared
    :class:`~data_structs.received_data.TransmittedData` under its
    internal lock; the raw line is also forwarded to
    :data:`~csv_logger.csv_logger` for persistent logging.

    Threading notes
    ---------------
    The ``running`` flag is a plain ``bool`` — safe for this pattern
    because it is only set ``False`` from the main thread and read by
    the single background thread.

    Attributes:
        port: Serial device path (e.g. ``/dev/ttyUSB0``).
        baudrate: Serial baud rate (default 115200).
        timeout: Serial read timeout in seconds.
        transmitted_data: Shared TransmittedData to populate.
        serial: ``serial.Serial`` instance (``None`` before ``start()``).
        thread: Background ``threading.Thread`` daemon.
        running: Flag controlling the read loop.
        last_data_time: ``time.time()`` of the most recently parsed packet.
    """
    # Store serial config and shared-data reference; defer actual port opening to start()
    def __init__(self, port, transmitted_data: TransmittedData, baudrate=115200, timeout=1):
        # Serial device path (e.g. /dev/ttyUSB0) — immutable after construction
        self.port = port
        # Baud rate matching the rocket telemetry firmware's UART configuration
        self.baudrate = baudrate
        # Read timeout prevents infinite blocking if the device disconnects mid-read
        self.timeout = timeout
        # Shared TransmittedData — the background thread writes into it under td.lock
        self.transmitted_data = transmitted_data
        # pyserial Serial object stays None until start() successfully opens the port
        self.serial = None
        # Background thread stays None until start() launches _read_loop
        self.thread = None
        # Control flag: set True by start(), False by stop(); read by _read_loop
        self.running = False
        # Wall-clock timestamp of the most recent successful parse — used for watchdog
        self.last_data_time = 0.0
        # Thread-safe queue holding raw serial lines for the GUI to drain each tick
        self.raw_queue: queue.Queue[str] = queue.Queue()

    # Open the serial port and launch the background daemon thread
    def start(self):
        try:
            # Blocking open — pyserial waits up to `timeout` seconds for the port to be ready
            self.serial = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        except serial.SerialException as e:
            # Catch permission-denied, port-not-found, or already-in-use
            logger.exception("Could not open serial port %s: %s", self.port, e)
            # Re-raise so main.py can fall back to demo mode if the port is unavailable
            raise
        # Signal _read_loop that it can begin processing serial data
        self.running = True
        # Daemon thread — won't block app exit; target is the infinite polling loop
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        # Start the thread immediately — it begins polling the serial port right away
        self.thread.start()

    # Graceful shutdown: stop loop, join thread, close port
    def stop(self):
        # Clear the running flag so _read_loop exits on its next iteration
        self.running = False
        # Only attempt join if start() was called and the thread was created
        if self.thread:
            # Wait up to 1s for _read_loop to notice the flag and terminate
            self.thread.join(timeout=1)
        # Only attempt close if start() was called and an open was attempted
        if self.serial:
            try:
                # Check before closing — double-close can log spurious errors
                if self.serial.is_open:
                    # Release the serial port so other tools or the next start() can use it
                    self.serial.close()
            except Exception:
                # Don't let a close failure propagate — just log it
                logger.exception("Error closing serial port!")

    # Infinite polling loop that runs on the daemon thread — reads and parses serial lines
    def _read_loop(self):
        # Check the running flag each iteration; exit promptly when stop() sets it False
        while self.running:
            # Guard: serial might be None (if open failed) or externally closed (USB unplugged)
            if not self.serial or not getattr(self.serial, "is_open", False):
                # Back off 100ms before rechecking — avoids busy-waiting on a dead port
                time.sleep(0.1)
                # Skip the rest and re-evaluate running + serial state
                continue
            try:
                # Non-blocking check: only call readline when bytes are actually buffered
                if self.serial.in_waiting:
                    # Read until newline, decode bytes→str ignoring undecodable bytes, strip CR/LF
                    line = self.serial.readline().decode(errors='ignore').strip()
                    # Skip empty lines (stray newlines, partial reads after reconnect)
                    if line:
                        # Parse the 15-field packet and populate TransmittedData under its lock
                        self.on_data(line)
            except serial.SerialException:
                # Catch pyserial I/O errors (port disconnected mid-read)
                logger.exception("Error reading from serial port!")
            except Exception:
                # Catch-all for any non-serial bug (memory, encoding, etc.)
                logger.exception("Unexpected error while reading from serial port!")
            # 10ms sleep yields CPU between polling cycles (~100 checks/second)
            time.sleep(0.01)

    # Parse a raw semicolon-delimited line and write all fields into TransmittedData
    def on_data(self, data: str):
        # Push raw line into the thread-safe queue so the GUI can display it like a terminal
        self.raw_queue.put(data)
        # Split on ';' — the rocket firmware uses semicolons as field delimiters
        split_data = data.split(';')
        # Accept 14 fields (seq;status;drive;temps;ax;ay;yaw;gyro;voltage;current;battery) or
        # 15 fields (seq;timestamp;status;drive;temps;ax;ay;yaw;gyro;voltage;current;battery)
        n = len(split_data)
        if n == 14:
            # 14-field format: no timestamp — use wall clock as synthetic timestamp
            sidx = 0   # telemetry data starts at index 0
            timestamp = int(time.time() * 1000)
        elif n == 15:
            # 15-field format: includes timestamp at index 1
            sidx = 1
            timestamp = int(split_data[1])
        else:
            logger.debug("Unexpected packet length: %d", n)
            return

        try:
            td = self.transmitted_data
            with td.lock:
                td.previous_packet_number = td.packet_number
                td.packet_number = int(split_data[0])

                td.previous_packet_timestamp = td.timestamp
                td.timestamp = timestamp

                # sidx=0 for 14-field, sidx=1 for 15-field
                td.status = int(split_data[sidx + 1])
                td.drive = float(split_data[sidx + 2])
                td.temperature_engine = int(float(split_data[sidx + 3]))
                td.temperature_battery = int(float(split_data[sidx + 4]))
                td.temperature_chip = int(float(split_data[sidx + 5]))
                td.lin_accel_x = float(split_data[sidx + 6])
                td.lin_accel_y = float(split_data[sidx + 7])
                td.euler = float(split_data[sidx + 8])
                td.gyro_z = float(split_data[sidx + 9])
                td.voltage = float(split_data[sidx + 10])
                td.current = float(split_data[sidx + 11])
                td.battery_voltage = float(split_data[sidx + 12])
                td.battery_percentage = float(split_data[sidx + 13])
            self.last_data_time = time.time()
            csv_logger.write(data)
        except (ValueError, IndexError) as e:
            logger.warning("Failed to parse (n=%d, split=%r): %s", n, split_data, e)
        except Exception:
            logger.exception("Unexpected error parsing data: %r", data)

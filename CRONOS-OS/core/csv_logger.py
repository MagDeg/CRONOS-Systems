"""Thread-safe CSV file logger for telemetry data.

Writes raw serial lines to a rolling CSV file.  All public methods
acquire an internal lock so the background
:class:`~serial_background_reading.SerialReader` thread can safely log
data without racing with GUI-triggered ``new_file()`` / ``close()``
calls.

.. py:data:: csv_logger
   Module-level singleton pre-configured for ``telemetry_log.csv``.
"""

# threading.Lock serialises file access between the background SerialReader and GUI thread
import threading
# os.path for building absolute paths and extracting filenames
import os

# Thread-safe CSV logger: all file operations are serialised by _lock
class CsvLogger:
    """Thread-safe writer for CSV telemetry logs.

    Opens, closes, and rotates CSV files.  All public methods use an
    internal ``threading.Lock`` so the background
    :class:`~serial_background_reading.SerialReader` thread can safely
    log data without racing with GUI-triggered ``new_file()`` calls.

    Attributes:
        _lock: threading.Lock serialising all file operations.
        _path: Absolute path to the current CSV file.
        _count: Number of lines written to the current file.
        _fp: Open file handle (``None`` when closed).
    """
    # Initialise with file path, zero count, and no open handle
    def __init__(self):
        # Lock that serialises all file I/O — safe for cross-thread callers
        self._lock = threading.Lock()
        # Default log path resolved to an absolute path from the working directory
        self._path = os.path.abspath("telemetry_log.csv")
        # Running count of lines written to the current file (for stats display)
        self._count = 0
        # File handle stays None until open() or new_file() is called
        self._fp = None

    # Expose the current CSV file path to callers (e.g., settings panel)
    @property
    def path(self):
        return self._path

    # Expose just the filename (not the full path) for compact display in the UI
    @property
    def basename(self):
        return os.path.basename(self._path)

    # Expose the current line count for the stats panel
    @property
    def count(self):
        return self._count

    # Rotate to a new CSV file — closes the old file and opens a fresh one under the lock
    def new_file(self, name: str):
        # Automatically append .csv extension if the caller omitted it
        name = name if name.endswith(".csv") else name + ".csv"
        with self._lock:
            # Close the current file before switching to the new one
            if self._fp is not None:
                self._fp.close()
                self._fp = None
            # Update path to the new (absolute) filename
            self._path = os.path.abspath(name)
            # Reset the line counter for the new file
            self._count = 0
            # Open in append mode so existing files aren't truncated, UTF-8 for broad compatibility
            self._fp = open(self._path, "a", encoding="utf-8")

    # Open the default CSV file (idempotent — no-op if already open)
    def open(self):
        with self._lock:
            # Already open — nothing to do, avoid re-opening and losing the write position
            if self._fp is not None:
                return
            # Append mode preserves any previous content in the file
            self._fp = open(self._path, "a", encoding="utf-8")
            # Reset and recount existing lines so count is accurate after re-open
            self._count = 0
            # Count every existing line in the file so the stats display is correct
            for _ in open(self._path, encoding="utf-8"):
                self._count += 1

    # Close the current CSV file — idempotent, safe to call multiple times
    def close(self):
        with self._lock:
            # Only close if there's an open handle
            if self._fp is not None:
                self._fp.close()
                # Mark handle as closed so open() can re-open later
                self._fp = None

    # Write a single telemetry line to the CSV file under the lock
    def write(self, line: str):
        with self._lock:
            # Silently drop lines when no file is open (e.g., before first open() call)
            if self._fp is None:
                return
            # Append the line with a newline; caller passes the line without trailing newline
            self._fp.write(line + "\n")
            # Flush immediately so the file on disk is never more than one line behind
            self._fp.flush()
            # Increment the running line count for the stats display
            self._count += 1

# Module-level singleton so SerialReader and GUI both log to the same CSV file
csv_logger = CsvLogger()

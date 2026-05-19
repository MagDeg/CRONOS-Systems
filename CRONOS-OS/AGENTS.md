# C.R.O.N.O.S. OS

Native Linux desktop telemetry dashboard for rocket/vehicle telemetry over serial. Built with PySide6 (Qt for Python) — no browser, no Dash, no integrated web engine.

## Entrypoint

`main.py` — creates a QApplication, loads Qt stylesheet from `assets/styles.qss`, builds the `MainWindow`, and starts a 200ms update timer. If `/dev/ttyUSB0` exists, a threaded `SerialReader` reads semicolon-delimited telemetry packets; otherwise demo data is generated internally.

## Architecture

| Directory | Role |
|-----------|------|
| `main.py` / `tick_loop.py` | Entrypoint + 500 ms update loop coordinator |
| `core/` | Data processing: `DisplayDataCalculator`, `SerialReader`, `CsvLogger`, `StatsTracker`, `DemoDataGenerator` |
| `data/` | Data models: `TransmittedData` (raw serial fields), `DisplayData` (computed display values), `MetricHistory` (ring buffer) |
| `tracking/` | Sub-system trackers: `PositionTracker`, `TripComputer`, `ErrorTracker`, `LapTimer`, `EnergyTracker` |
| `definitions/` | Error code definitions: `ERROR_MAP`, `ERROR_MODULES`, `ALL_MODULES` |
| `ui/components/` | Reusable QWidget primitives: `SpeedGaugeWidget`, `HeadingWidget`, `RouteWidget`, `ToggleSwitch` |
| `ui/panels/` | Dashboard panel widgets for each data section (speed, drive, electric, temperature, accel/g-force, network, time, settings) |
| `ui/popups/` | Non-modal `QDialog` subclasses: gyro, route, module status, trip, trends, graph |
| `ui/layouts/` | PySide6 widget trees composing the full window: `TopBar`, `MainView`, `RightSidebar`, `StatsLayout` |
| `assets/` | `styles.qss` — Qt Style Sheet (no CSS build step) |

`main.py` uses `SerialReader` (text protocol), *not* `SerialCommunication` (binary protocol).

## Running

```
pip install PySide6 pyserial
python main.py
```

No package manager config. No virtualenv required — system-wide or venv install works.

## Key Differences from Original (Dash)

- **No browser, no server** — pure Qt widgets render natively via QPainter and the Fusion style.
- **Custom arc gauges** — `ArcGaugeWidget` paints 270° arc gauges with QPainter, replacing Plotly indicator gauges. Faster, lighter, no JavaScript.
- **Signal/slot data flow** — instead of Dash callbacks, a `QTimer` ticks every 200ms, reads from `TransmittedData` (locked), runs `DisplayDataCalculator`, and calls `update_from_data()` on every widget.
- **Thread safety** — `TransmittedData` has a `threading.Lock` that the `SerialReader` background thread acquires when writing fields.
- **QSS stylesheet** — `assets/styles.qss` mirrors the original CSS theme (dark HUD, cyan accents) and is loaded on startup.
- **Example simulation** — when no serial port is detected, `DemoDataGenerator` produces realistic random telemetry every tick.

## Structure Notes

- `callbacks/` files are retained as structural stubs matching the original project layout. Actual data flow is handled by `register_data_bindings.py` which returns a closure called on each timer tick.
- `example.py` is removed — demo mode is built into `main.py` via `DemoDataGenerator`.
- No tests, no CI, no linting/formatting config.

## Recommended Resolution

1440×900 or larger. The layout uses fixed-width sidebars (240px each) and flex-like stretch panels in the center.

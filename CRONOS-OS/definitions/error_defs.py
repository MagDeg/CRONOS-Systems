"""Error code definitions for the CRONOS telemetry system.

Maps numeric error codes (0–20) to human-readable name/description
pairs and groups each code under the hardware module that produced it.

.. py:data:: ERROR_MODULES
   ``{code: module_name}`` — lookup a module from an error code.

.. py:data:: ERROR_MAP
   ``{code: (name, description)}`` — full error catalogue.

.. py:data:: ALL_MODULES
   Sorted list of every known module name.
"""

# Map each error code to the hardware module that emits it, so the UI can group errors by subsystem
ERROR_MODULES = {
    # Radio subsystem codes
    1: "Radio", 2: "Radio", 3: "Radio", 15: "Radio",
    # SD-card subsystem codes
    4: "SD Card", 5: "SD Card", 6: "SD Card", 16: "SD Card",
    # Engine-sensor subsystem codes
    7: "Engine Sensor", 9: "Engine Sensor",
    # Battery-sensor subsystem codes
    8: "Battery Sensor", 10: "Battery Sensor",
    # On-board chip sensor subsystem code
    11: "Chip Sensor",
    # INA219 current/voltage sensor subsystem codes
    12: "INA219", 13: "INA219", 14: "INA219",
    # BNO055 IMU subsystem code
    17: "BNO IMU",
    # Hall-effect speed sensor subsystem code
    19: "Hall Sensor",
    # MAX17048 fuel-gauge subsystem code
    20: "MAX17048",
}

# Sorted list of every known module name, used by the UI to render module-status checkboxes in a consistent order
ALL_MODULES = ["Radio", "SD Card", "Engine Sensor", "Battery Sensor",
               "Chip Sensor", "INA219", "BNO IMU", "Hall Sensor", "MAX17048"]

# Full error catalogue mapping each numeric code to a machine-readable name and a human-readable description
ERROR_MAP = {
    # Special sentinel: code 0 means everything is nominal
    0:  ("NO_ISSUES", "No issues detected"),
    # Radio initialisation failure on startup
    1:  ("RADIO_INIT_FAILED", "Radio initialization failed"),
    # Telemetry data could not be transmitted over the radio link
    2:  ("DATA_TRANSMISSION_FAILED", "Data transmission failed"),
    # Radio signal strength has dropped below the usable threshold
    3:  ("BAD_SIGNAL_STRENGTH", "Bad signal strength"),
    # SD card could not be initialised — logging is unavailable
    4:  ("SD_INIT_FAILED", "SD card initialization failed"),
    # SD card file could not be opened for writing — logging is unavailable
    5:  ("SD_FILE_OPEN_FAILED", "SD file open failed"),
    # Write to the SD card file failed — possible card full or filesystem error
    6:  ("SD_WRITE_FAILED", "SD write failed"),
    # Engine temperature sensor is not responding
    7:  ("ENGINE_SENSOR_NOT_FOUND", "Engine sensor not found"),
    # Battery temperature sensor is not responding
    8:  ("BATTERY_SENSOR_NOT_FOUND", "Battery sensor not found"),
    # Engine sensor is detected but reports out-of-range or invalid values
    9:  ("INVALID_ENGINE_SENSOR_VALUES", "Invalid engine sensor values"),
    # Battery sensor is detected but reports out-of-range or invalid values
    10: ("INVALID_BATTERY_SENSOR_VALUES", "Invalid battery sensor values"),
    # On-board chip sensor is detected but reports out-of-range or invalid values
    11: ("INVALID_CHIP_SENSOR_VALUES", "Invalid chip sensor values"),
    # INA219 power-monitor IC failed to initialise on the I²C bus
    12: ("INA219_INIT_FAILED", "INA219 (current/voltage) init failed"),
    # INA219 current readings are out of expected range
    13: ("INVALID_CURRENT_VALUES", "Invalid current values"),
    # INA219 voltage readings are out of expected range
    14: ("INVALID_VOLTAGE_VALUES", "Invalid voltage values"),
    # No radio link established — all radio errors cascade from this
    15: ("NO_RADIO_CONNECTION", "No radio connection"),
    # Attempted SD write but the file handle is not open
    16: ("SD_FILE_NOT_OPEN", "SD file not open"),
    # BNO055 IMU failed to initialise on the I²C bus
    17: ("BNO_INIT_FAILED", "BNO (IMU) init failed"),
    # Hall-effect speed sensor is not detected by the microcontroller
    19: ("HALL_SENSOR_NOT_DETECTED", "Hall sensor not detected"),
    # MAX17048 fuel-gauge IC failed to initialise on the I²C bus
    20: ("MAX17048_INIT_FAILED", "MAX17048 (fuel gauge) init failed"),
}

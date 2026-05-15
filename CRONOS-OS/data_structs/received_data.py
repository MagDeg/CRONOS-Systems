from dataclasses import dataclass

@dataclass
class TransmittedData:
    packet_number: int
    previous_packet_number: int
    timestamp: int
    previous_packet_timestamp: int
    status: int

    drive: float

    temperature_engine: int
    temperature_battery: int
    temperature_chip: int

    lin_accel_x: float
    lin_accel_y: float
    euler: float
    gyro_z: float

    voltage: float
    current: float

    temperature_5: float
    temperature_4: float
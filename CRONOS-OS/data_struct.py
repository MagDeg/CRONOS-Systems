from dataclasses import dataclass

@dataclass
class TransmittedData:
    identifier: int = 0
    status: int = 0
    drive: float = 0.0
    temperature_engine: int = 0
    temperature_battery: int = 0
    temperature_chip: int = 0
    acceleration: float = 0.0
    voltage: float = 0.0
    current: float = 0.0
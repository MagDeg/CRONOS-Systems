from datetime import datetime
from dataclasses import dataclass

@dataclass
class DisplayData:
    package_loss: float #%
    delay: int # ms
    connection_state: bool
    acceleration: float #m/s²
    g_force: float #g
    distance: float #km
    velocity: float #km/h
    rpm: float #U/min
    voltage: float #V
    current: float  #A
    power: float #W
    temperature_engine: int #°C
    temperature_battery: int #°C
    temperature_chip: int #°C
    elapsed_time: datetime
    remaining_time: datetime

    list_with_errors: list[str]
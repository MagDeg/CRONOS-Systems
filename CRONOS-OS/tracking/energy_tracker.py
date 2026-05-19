"""Energy tracker — integrates power over time to compute kWh.

The energy value is written directly into ``DisplayData.energy_kwh``.
"""

# DisplayData is the shared mutable data bus that TickLoop reads each frame
from data.displayed_data import DisplayData

# Conversion factor: 1 Wh = 3600 Ws, so 1 kWh = 3 600 000 Ws
_WS_PER_KWH: float = 3_600_000.0


class EnergyTracker:
    """Integrates electrical power (watts) over time to accumulate kWh."""

    def tick(self, dt: float, power_w: float, display: DisplayData) -> None:
        """Accumulate energy consumption.

        Args:
            dt: Time delta in seconds.
            power_w: Instantaneous power in watts.
            display: Mutable DisplayData to write into.
        """
        # power (W) × dt (s) = energy (Ws); divide by 3 600 000 to convert Ws → kWh
        display.energy_kwh += power_w * dt / _WS_PER_KWH

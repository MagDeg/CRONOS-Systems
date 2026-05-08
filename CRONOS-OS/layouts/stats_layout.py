from components.accel_gforce_panel import AccelGForceDistance
from components.panels import *
from components.electric_values import combinedPowerPanel
from components.speed_drive_panel import CompactSpeedDriveGauges
from components.speed_gauge import combinedSpeedGauge
from components.temperature_panel import combinedTempPanel


def get_stats_layout():
    return html.Div([
        html.Div([
            Panel(
                index=0,
                content=CompactSpeedDriveGauges(index=3, speed_value=100, rpm_value=100),
                widget="gauge",
                link="/speed",
                config={"unit":"km/h", "max":200},
            ),
            Panel(
                index=1,
                content=combinedPowerPanel(
                    index=0,
                    voltage=12.6, voltage_unit="V", voltage_stats=(12.5, 12.3, 12.8),
                    current=3.2, current_unit="A", current_stats=(3.1, 2.8, 4.0),
                    power=40.3, power_unit="W", power_stats=(39.8, 35.0, 45.2),
                    title="Elektrik"
                ),
                widget="power",
                link="/power",
                config={"unit": "electrical"}
            ),
            Panel(
                index=2,
                content=combinedTempPanel(index=1),
                widget="temp",
                link="/temperatures",
                config={"index":1},
            ),
        ], className="panel-row"),

        html.Div([
            Panel(
                index=3,
                content=AccelGForceDistance(index=4, vertical_gap="50px"),
                widget="gauge",
                link="/panel1",
                config={"unit": "km/h", "max": 200},
            ),
            Panel(
                index=4,
                content=None,
                widget="gauge",
                link="/panel1",
                config={"unit": "km/h", "max": 200},
            ),
            Panel(
                index=5,
                content=None,
                widget="gauge",
                link="/panel1",
                config={"unit": "km/h", "max": 200},
            ),
        ], className="panel-row")
    ], className="main")
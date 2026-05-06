

from components.panels import *
from components.speed_gauge import combinedSpeedGauge


def get_stats_layout():
    return html.Div([
        html.Div([
            Panel(
                index=0,
                content=combinedSpeedGauge(index=0,value=120, avg=80, min_val=50, max_val=200,),
                widget="gauge",
                link="/panel1",
                config={"unit":"km/h", "max":200},
            ),
            Panel(
                index=1,
                content=combinedSpeedGauge(index=1,value=120, avg=80, min_val=50, max_val=200),
                widget="gauge",
                link="/panel1",
                config={"unit": "km/h", "max": 200},
            ),
            Panel(
                index=2,
                content=combinedSpeedGauge(index=2,value=120, avg=80, min_val=50, max_val=2000),
                widget="gauge",
                link="/panel1",
                config={"unit": "km/h", "max": 200},
            ),
        ], className="panel-row"),

        html.Div([
            Panel(
                index=3,
                content=combinedSpeedGauge(index=3,value=120, avg=80, min_val=50, max_val=200),
                widget="gauge",
                link="/panel1",
                config={"unit": "km/h", "max": 200},
            ),
            Panel(
                index=4,
                content=combinedSpeedGauge(index=4,value=120, avg=80, min_val=50, max_val=200),
                widget="gauge",
                link="/panel1",
                config={"unit": "km/h", "max": 200},
            ),
            Panel(
                index=5,
                content=combinedSpeedGauge(index=5,value=120, avg=80, min_val=50, max_val=200),
                widget="gauge",
                link="/panel1",
                config={"unit": "km/h", "max": 200},
            ),
        ], className="panel-row")
    ], className="main")
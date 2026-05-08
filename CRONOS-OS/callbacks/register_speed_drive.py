
import random
from dash import Input, Output, MATCH
import dash
import plotly.graph_objects as go

def _gauge_figure_with_suffix(value, max_value, suffix, color,
                              number_size=22, gauge_thickness=0.20, height=120):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'font': {'size': number_size}, 'suffix': suffix},
        title={'text': "", 'font': {'size': 10}},
        gauge={
            'axis': {'range': [0, max_value], 'visible': False},
            'bar': {'color': color, 'thickness': gauge_thickness},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [{'range': [0, max_value], 'color': "#222"}],
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "white"},
        margin=dict(l=0, r=0, t=0, b=0),
        height=height
    )
    return fig

def register_speed_drive_callbacks(app):
    """
    Registriert MATCH-Callbacks für Speed- und Drive-Gauges.
    Erwartet im Layout:
      - dcc.Interval(id='gauge-update-interval', ...)
      - dcc.Store(id={'type':'panel-config','index': <index>}, data={'index': <index>})
      - Graphs mit IDs {'type':'gauge','metric':'speed'|'drive','index': <index>}
      - Stat-Outputs mit IDs {'type':'stat-avg'|'stat-min'|'stat-max','metric':...,'index': <index>}
    """

    @app.callback(
        Output({'type':'gauge','metric':'speed','index': MATCH}, 'figure'),
        Output({'type':'stat-avg','metric':'speed','index': MATCH}, 'children'),
        Output({'type':'stat-min','metric':'speed','index': MATCH}, 'children'),
        Output({'type':'stat-max','metric':'speed','index': MATCH}, 'children'),
        Input('gauge-update-interval', 'n_intervals'),
        Input({'type':'panel-config','index': MATCH}, 'data'),
        prevent_initial_call=False
    )
    def _update_speed(n_intervals, panel_config):
        if not panel_config:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Zufallswerte für Testzwecke
        speed = round(random.uniform(0, 180), 1)
        avg = f"{round(max(0, speed - random.uniform(0, 8)), 1)}"
        mn  = f"{round(max(0, speed - random.uniform(5, 20)), 1)}"
        mx  = f"{round(speed + random.uniform(3, 25), 1)}"

        fig = _gauge_figure_with_suffix(speed, max_value=200, suffix=" km/h", color="#00d4ff",
                                        number_size=22, gauge_thickness=0.20, height=120)
        return fig, avg, mn, mx

    @app.callback(
        Output({'type':'gauge','metric':'drive','index': MATCH}, 'figure'),
        Output({'type':'stat-avg','metric':'drive','index': MATCH}, 'children'),
        Output({'type':'stat-min','metric':'drive','index': MATCH}, 'children'),
        Output({'type':'stat-max','metric':'drive','index': MATCH}, 'children'),
        Input('gauge-update-interval', 'n_intervals'),
        Input({'type':'panel-config','index': MATCH}, 'data'),
        prevent_initial_call=False
    )
    def _update_drive(n_intervals, panel_config):
        if not panel_config:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Zufallswerte für Testzwecke (RPM)
        rpm = int(random.uniform(600, 5200))
        avg = f"{int(max(0, rpm - random.uniform(50, 300)))}"
        mn  = f"{int(max(0, rpm - random.uniform(200, 800)))}"
        mx  = f"{int(rpm + random.uniform(100, 900))}"

        fig = _gauge_figure_with_suffix(rpm, max_value=8000, suffix=" U/min", color="#00ffa6",
                                        number_size=22, gauge_thickness=0.20, height=120)
        return fig, avg, mn, mx

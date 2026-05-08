# callbacks/accel_gforce_distance_compact_final_callbacks.py
import random
import dash
from dash import Input, Output, MATCH

def _gauge_figure_with_suffix(value, max_value, suffix, color,
                              number_size=22, gauge_thickness=0.20, height=120):
    import plotly.graph_objects as go
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

def register_accel_gforce_distance_callbacks(app):
    """
    MATCH-Callbacks für das kompakte Panel.
    Erwartet im Layout:
      - dcc.Interval(id='gauge-update-interval', ...)
      - dcc.Store(id={'type':'panel-config','index': <index>}, data={'index': <index>})
    Outputs (MATCH):
      - Gauge figure: Output({'type':'gauge','metric':'accel','index': MATCH}, 'figure')
      - G-Force value: Output({'type':'gforce-value','index': MATCH}, 'children')
      - Distance value: Output({'type':'distance-value','index': MATCH}, 'children')
    """

    @app.callback(
        Output({'type':'gauge','metric':'accel','index': MATCH}, 'figure'),
        Input('gauge-update-interval', 'n_intervals'),
        Input({'type':'panel-config','index': MATCH}, 'data'),
        prevent_initial_call=False
    )
    def _update_accel_figure(n_intervals, panel_config):
        if not panel_config:
            return dash.no_update
        # Zufälliger Beschleunigungswert (m/s²) realistisch zwischen 0 und 30
        accel = round(random.uniform(0.0, 30.0), 2)
        fig = _gauge_figure_with_suffix(
            accel,
            max_value=30.0,
            suffix=" m/s²",
            color="#ff7f50",
            number_size=22,
            gauge_thickness=0.20,
            height=120
        )
        return fig

    @app.callback(
        Output({'type':'gforce-value','index': MATCH}, 'children'),
        Input('gauge-update-interval', 'n_intervals'),
        Input({'type':'panel-config','index': MATCH}, 'data'),
        prevent_initial_call=False
    )
    def _update_gforce_value(n_intervals, panel_config):
        if not panel_config:
            return dash.no_update
        # Zufälliger G‑Wert zwischen 0.00 und 5.50
        g = round(random.uniform(0.00, 5.50), 2)
        return f"{g:.2f}"

    @app.callback(
        Output({'type':'distance-value','index': MATCH}, 'children'),
        Input('gauge-update-interval', 'n_intervals'),
        Input({'type':'panel-config','index': MATCH}, 'data'),
        prevent_initial_call=False
    )
    def _update_distance_value(n_intervals, panel_config):
        if not panel_config:
            return dash.no_update
        # Zufälliger Distanzwert (z. B. km) zwischen 0.0 und 120.0
        dist = round(random.uniform(0.0, 120.0), 1)
        return f"{dist:.1f}"

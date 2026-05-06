# callbacks/gauge_callbacks.py
from dash import Input, Output, MATCH
import dash
import plotly.graph_objects as go
import random

def register_gauge_callbacks(app):
    @app.callback(
        Output({'type': 'gauge', 'index': MATCH}, 'figure'),
        Output({'type': 'stat-avg', 'index': MATCH}, 'children'),
        Output({'type': 'stat-min', 'index': MATCH}, 'children'),
        Output({'type': 'stat-max', 'index': MATCH}, 'children'),
        Input('gauge-update-interval', 'n_intervals'),
        Input({'type': 'panel-config', 'index': MATCH}, 'data'),
        prevent_initial_call=False,
        allow_duplicate=True
    )
    def update_gauge(n_intervals, config):
        cfg = config or {}
        if cfg.get("widget") != "gauge":
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        max_axis = cfg.get("max", 200)
        unit = cfg.get("unit", "")
        bar_color = cfg.get("gauge_style", {}).get("bar_color", "#00d4ff")
        title_text = cfg.get("title", unit)

        # Hier echte Daten holen (z.B. fetch_by_source(cfg["source"])) — aktuell Demowerte:
        new_value = 80 + (max_axis - 80) * random.random()
        avg_val = new_value * 0.9
        min_val = max(0, new_value - 20 * random.random())
        max_val_calc = min(max_axis, new_value + 20 * random.random())

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=new_value,
            number={'font': {'size': 40}, 'suffix': f" {unit}" if unit else ""},
            title={'text': title_text, 'font': {'size': 16}},
            gauge={
                'axis': {'range': [0, max_axis], 'visible': False},
                'bar': {'color': bar_color, 'thickness': 0.3},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 0,
                'steps': [{'range': [0, max_axis], 'color': "#222"}],
            }
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font={'color': "white"},
            margin=dict(l=0, r=0, t=0, b=0),
            autosize=True
        )

        return fig, f"{avg_val:.1f}", f"{min_val:.1f}", f"{max_val_calc:.1f}"

# components/speed_gauge.py
from dash import html, dcc
import plotly.graph_objects as go

def SpeedGaugeGraph(index, value=120):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'font': {'size': 40}},
        title={'text': "km/h", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, 200], 'visible': False},
            'bar': {'color': "#00d4ff", 'thickness': 0.3},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [{'range': [0, 200], 'color': "#222"}],
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, margin=dict(l=0, r=0, t=0, b=0))
    return dcc.Graph(
        id={'type': 'gauge', 'index': index},
        figure=fig,
        config={"displayModeBar": False},
        style={"width": "100%", "height": "100%", "flex": "1"}
    )

def SpeedGaugeStats(index, avg=100, min_val=80, max_val=150):
    value_style = {"fontSize": "20px", "textAlign": "center", "lineHeight": "24px", "minWidth": "40px"}
    label_style = {"fontSize": "12px", "opacity": 0.6, "textAlign": "center"}
    return html.Div([
        html.Div([html.Div("AVG", style=label_style), html.Div(f"{avg}", id={'type': 'stat-avg', 'index': index}, style=value_style)]),
        html.Div([html.Div("MIN", style=label_style), html.Div(f"{min_val}", id={'type': 'stat-min', 'index': index}, style=value_style)]),
        html.Div([html.Div("MAX", style=label_style), html.Div(f"{max_val}", id={'type': 'stat-max', 'index': index}, style=value_style)])
    ], style={"display": "flex", "flexDirection": "row", "alignItems": "center", "justifyContent": "space-around", "marginTop": "4px", "width": "100%"})

def combinedSpeedGauge(index, value=120, avg=100, min_val=80, max_val=150):
    return html.Div([
        html.Div("Geschwindigkeit", style={"height": "30px", "flex": "0 0 auto", "display": "flex", "alignItems": "center", "justifyContent": "center"}),
        html.Div(SpeedGaugeGraph(index=index, value=value), style={"flex": "1 1 auto", "minHeight": 0, "overflow": "hidden"}),
        html.Div(SpeedGaugeStats(index=index, avg=avg, min_val=min_val, max_val=max_val), style={"height": "60px", "flex": "0 0 auto", "display": "flex", "alignItems": "center", "justifyContent": "space-around"})
    ], style={"display": "flex", "flexDirection": "column", "height": "100%", "minHeight": 0, "overflow": "hidden"})

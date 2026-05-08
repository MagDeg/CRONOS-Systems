# components/drive_gauge.py
from dash import html, dcc
import plotly.graph_objects as go

def DriveGaugeGraph(index, value=1200, rpm_max=8000):
    """
    Plotly Indicator Gauge für Drehzahl (RPM / U/min).
    - index: id für das dcc.Graph (wiederverwendbar mit MATCH)
    - value: aktuelle Drehzahl (Default 1200)
    - rpm_max: obere Skala (Default 8000)
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'font': {'size': 40}},
        title={'text': "U/min", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, rpm_max], 'visible': False},
            'bar': {'color': "#00d4ff", 'thickness': 0.3},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [{'range': [0, rpm_max], 'color': "#222"}],
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, margin=dict(l=0, r=0, t=0, b=0))
    return dcc.Graph(
        id={'type': 'gauge', 'index': index, 'metric': 'drive'},
        figure=fig,
        config={"displayModeBar": False},
        style={"width": "100%", "height": "100%", "flex": "1"}
    )

def DriveGaugeStats(index, avg=1000, min_val=800, max_val=5000):
    """
    Kleine Statistikzeile unter dem Gauge: AVG / MIN / MAX
    Pattern-IDs:
      - {'type':'stat-avg','index': index}
      - {'type':'stat-min','index': index}
      - {'type':'stat-max','index': index}
    """
    value_style = {"fontSize": "20px", "textAlign": "center", "lineHeight": "24px", "minWidth": "40px", "color":"white"}
    label_style = {"fontSize": "12px", "opacity": 0.6, "textAlign": "center", "color":"white"}
    return html.Div([
        html.Div([html.Div("AVG", style=label_style), html.Div(f"{avg}", id={'type': 'stat-avg', 'index': index}, style=value_style)]),
        html.Div([html.Div("MIN", style=label_style), html.Div(f"{min_val}", id={'type': 'stat-min', 'index': index}, style=value_style)]),
        html.Div([html.Div("MAX", style=label_style), html.Div(f"{max_val}", id={'type': 'stat-max', 'index': index}, style=value_style)])
    ], style={"display": "flex", "flexDirection": "row", "alignItems": "center", "justifyContent": "space-around", "marginTop": "4px", "width": "100%"})

def combinedDriveGauge(index, value=1200, avg=1000, min_val=800, max_val=5000, rpm_max=8000):
    """
    Kombiniertes Drive‑Gauge: Header + Gauge + Stats
    - identisch im Layout zur Speed‑Komponente, nur für Drehzahl
    """
    return html.Div([
        html.Div("Drehzahl", style={"height": "30px", "flex": "0 0 auto", "display": "flex", "alignItems": "center", "justifyContent": "center", "color":"white"}),
        html.Div(DriveGaugeGraph(index=index, value=value, rpm_max=rpm_max), style={"flex": "1 1 auto", "minHeight": 0, "overflow": "hidden"}),
        html.Div(DriveGaugeStats(index=index, avg=avg, min_val=min_val, max_val=max_val), style={"height": "60px", "flex": "0 0 auto", "display": "flex", "alignItems": "center", "justifyContent": "space-around"})
    ], style={"display": "flex", "flexDirection": "column", "height": "100%", "minHeight": 0, "overflow": "hidden"})

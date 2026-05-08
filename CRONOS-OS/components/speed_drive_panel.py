# components/compact_speed_drive_gauges_in_gauge_only.py
from dash import html, dcc
import plotly.graph_objects as go

def _gauge_figure_with_suffix(value, max_value, suffix,
                              bar_color="#00d4ff",
                              number_size=22, gauge_thickness=0.20, height=120):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'font': {'size': number_size}, 'suffix': suffix},
        title={'text': "", 'font': {'size': 10}},
        gauge={
            'axis': {'range': [0, max_value], 'visible': False},
            'bar': {'color': bar_color, 'thickness': gauge_thickness},
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

def CompactSpeedDriveGauges(index,
                                       speed_value=0.0, speed_max=200,
                                       rpm_value=0, rpm_max=8000,
                                       speed_color="#00d4ff", rpm_color="#00ffa6",
                                       gauge_height=120, number_size=22,
                                       vertical_gap="18px"):
    """
    Kompaktes, vertikal gestapeltes Panel mit zwei Gauges.
    - Einheiten werden als Suffix in der Gauge-Number angezeigt.
    - Keine zusätzlichen Value/Unit-Elemente oberhalb der Gauges.
    - Neuer Parameter vertical_gap steuert den Abstand zwischen den Gauges (z.B. "18px").
    Pattern-IDs (MATCH-kompatibel):
      * Graphs: {'type':'gauge','metric':'speed'|'drive','index': index}
      * Stats:  {'type':'stat-avg'|'stat-min'|'stat-max','metric':...,'index': index}
    """
    container_style = {
        "display": "flex",
        "flexDirection": "column",
        "height": "100%",
        "minHeight": 0,
        "overflow": "hidden",
        "boxSizing": "border-box",
        "gap": "8px",
        "padding": "6px",
        "color": "white"
    }

    header = html.Div("Fahrdaten", style={
        "height": "28px",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "fontSize": "13px",
        "color": "white"
    })

    def _stats_row(metric):
        value_style = {"fontSize": "12px", "textAlign": "center", "lineHeight": "14px", "color": "white"}
        label_style = {"fontSize": "10px", "opacity": 0.6, "textAlign": "center", "color": "white"}
        return html.Div([
            html.Div([html.Div("AVG", style=label_style), html.Div("-", id={'type':'stat-avg','metric':metric,'index':index}, style=value_style)], style={"flex":"1"}),
            html.Div([html.Div("MIN", style=label_style), html.Div("-", id={'type':'stat-min','metric':metric,'index':index}, style=value_style)], style={"flex":"1"}),
            html.Div([html.Div("MAX", style=label_style), html.Div("-", id={'type':'stat-max','metric':metric,'index':index}, style=value_style)], style={"flex":"1"})
        ], style={"display":"flex","flexDirection":"row","gap":"6px","width":"100%","boxSizing":"border-box","padding":"4px 0"})

    # --- Speed Block (oben) ---
    speed_label = html.Div("Geschwindigkeit", style={
        "fontSize": "12px",
        "color": "white",
        "opacity": 0.95,
        "textAlign": "center",
        "paddingTop": "2px"
    })

    speed_fig = _gauge_figure_with_suffix(speed_value, speed_max, " km/h",
                                          bar_color=speed_color,
                                          number_size=number_size,
                                          gauge_thickness=0.20,
                                          height=gauge_height)

    speed_graph = dcc.Graph(
        id={'type': 'gauge', 'metric': 'speed', 'index': index},
        figure=speed_fig,
        config={"displayModeBar": False},
        style={"width": "100%", "height": f"{gauge_height}px", "flex": "0 0 auto"}
    )

    speed_stats = _stats_row('speed')
    speed_block = html.Div([speed_label, speed_graph, speed_stats],
                           style={"display":"flex","flexDirection":"column","width":"100%","boxSizing":"border-box"})

    # Spacer zwischen den Gauges (kontrollierbar über vertical_gap)
    spacer = html.Div(style={"height": vertical_gap, "flex": "0 0 auto"})

    # --- Drive Block (unten) ---
    rpm_label = html.Div("Drehzahl", style={
        "fontSize": "12px",
        "color": "white",
        "opacity": 0.95,
        "textAlign": "center",
        "paddingTop": "2px"
    })

    drive_fig = _gauge_figure_with_suffix(rpm_value, rpm_max, " U/min",
                                          bar_color=rpm_color,
                                          number_size=number_size,
                                          gauge_thickness=0.20,
                                          height=gauge_height)

    drive_graph = dcc.Graph(
        id={'type': 'gauge', 'metric': 'drive', 'index': index},
        figure=drive_fig,
        config={"displayModeBar": False},
        style={"width": "100%", "height": f"{gauge_height}px", "flex": "0 0 auto"}
    )

    drive_stats = _stats_row('drive')
    drive_block = html.Div([rpm_label, drive_graph, drive_stats],
                           style={"display":"flex","flexDirection":"column","width":"100%","boxSizing":"border-box"})

    return html.Div([header, speed_block, spacer, drive_block], style=container_style)

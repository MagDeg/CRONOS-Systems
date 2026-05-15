from dash import html, dcc
import plotly.graph_objs as go
from datetime import datetime

def _value_with_unit(value_id, unit_id, value, unit):
    value_style = {
        "fontSize": "clamp(20px, 4vw, 36px)",
        "fontWeight": "700",
        "lineHeight": "1",
        "margin": "0",
        "padding": "0",
        "color": "white",
        "display": "inline-block",
        "verticalAlign": "middle"
    }
    unit_style = {
        "fontSize": "clamp(11px, 1.2vw, 14px)",
        "opacity": 0.9,
        "marginLeft": "6px",
        "display": "inline-block",
        "verticalAlign": "middle",
        "color": "white"
    }
    return html.Div([
        html.Span(value, id=value_id, style=value_style),
        html.Span(unit, id=unit_id, style=unit_style)
    ], style={"display":"flex","alignItems":"center","justifyContent":"center","gap":"6px","width":"100%"})


def _status_card(status_id, text_id, detail_id, initial_status="disconnected"):
    """
    Zentrierte Status-Kachel:
      - Header "Verbindungsstatus"
      - Lampe (Punkt) und Statustext nebeneinander, zentriert
      - Detailkachel (zeigt 'Letzte Prüfung')
    """
    wrapper = {
        "display":"flex",
        "flexDirection":"column",
        "alignItems":"center",
        "justifyContent":"center",
        "gap":"8px",
        "padding":"8px",
        "width":"100%"
    }
    header_style = {"fontSize":"13px","color":"white","opacity":0.95,"fontWeight":"600","textAlign":"center"}
    # Default-Lampenstil (wird per Callback überschrieben)
    lamp_style = {
        "width":"14px",
        "height":"14px",
        "borderRadius":"50%",
        "background":"#ff4d4f" if initial_status=="disconnected" else ("#ffb020" if initial_status=="degraded" else "#2ecc71"),
        "boxShadow":"0 0 8px rgba(0,0,0,0.45)",
        "display":"inline-block",
        "verticalAlign":"middle"
    }
    status_text_style = {"fontSize":"13px","color":"white","opacity":0.95,"textAlign":"center","fontWeight":"600","verticalAlign":"middle","marginLeft":"8px"}
    detail_card_style = {
        "background":"rgba(255,255,255,0.02)",
        "border":"1px solid rgba(255,255,255,0.03)",
        "borderRadius":"8px",
        "padding":"6px 10px",
        "minWidth":"160px",
        "textAlign":"center",
        "color":"white",
        "fontSize":"12px",
        "opacity":0.95
    }

    # Row mit Lampe + Text nebeneinander, zentriert
    status_row = html.Div([
        html.Div(id=status_id, style=lamp_style),
        html.Div(initial_status.capitalize(), id=text_id, style=status_text_style)
    ], style={"display":"flex","flexDirection":"row","alignItems":"center","justifyContent":"center","gap":"6px","width":"100%"})

    return html.Div([
        html.Div("Verbindungsstatus", style=header_style),
        status_row,
        html.Div(id=detail_id, children=[
            html.Div("Letzte Prüfung: -")
        ], style=detail_card_style)
    ], style=wrapper)


def _delay_sparkline_graph_with_value(graph_id, value_id, values=None, stroke="#00aaff", y_label="ms"):
    if values is None:
        values = [0]*10
    fig = go.Figure(go.Scatter(
        x=list(range(len(values))),
        y=values,
        mode="lines",
        line=dict(color=stroke, width=2),
        hoverinfo="y"
    ))
    # kompatible y-axis title-Definition (title as dict) um Plotly-Version-Probleme zu vermeiden
    fig.update_layout(
        margin=dict(l=6, r=6, t=4, b=4),
        xaxis=dict(visible=False),
        yaxis=dict(
            visible=True,
            title=dict(text=y_label, font=dict(size=10, color="#ffffff")),
            tickfont=dict(size=10, color="#cccccc")
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=56
    )
    graph = dcc.Graph(id=graph_id, figure=fig, config={"displayModeBar": False}, style={"width":"100%","height":"56px"})
    value_style = {"fontSize":"12px","color":"white","opacity":0.95,"textAlign":"center","padding":"2px 0"}
    value_div = html.Div(f"{values[-1]} ms" if values else "-", id=value_id, style=value_style)
    return html.Div([graph, value_div], style={"display":"flex","flexDirection":"column","alignItems":"stretch","gap":"6px","width":"100%"})


def _packet_bar_container(fill_id, percent=0.0, fill_color="#00aaff"):
    container_style = {
        "width": "100%",
        "height": "8px",
        "background": "rgba(255,255,255,0.03)",
        "borderRadius": "8px",
        "overflow": "hidden",
        "boxSizing": "border-box"
    }
    fill_style = {
        "width": f"{max(0, min(100, float(percent)))}%",
        "height": "100%",
        "background": fill_color,
        "transition": "width 0.2s linear, background 0.2s linear",
        "borderRadius": "8px"
    }
    return html.Div([html.Div(style=container_style, children=[html.Div(id=fill_id, style=fill_style)])],
                    style={"padding":"6px 8px","boxSizing":"border-box","width":"100%"})


def PacketLossMetricBlockCompact(index, metric, label="Packet Loss", value=0.0, unit="%", min_val=0.0, max_val=100.0, accent_color="#00aaff"):
    card_style = {
        "backgroundColor": "rgba(255,255,255,0.015)",
        "borderRadius": "10px",
        "padding": "8px 10px",
        "boxSizing": "border-box",
        "width": "100%",
        "display": "flex",
        "flexDirection": "column",
        "gap": "8px",
        "position": "relative",
        "overflow": "hidden"
    }
    left_accent = html.Div(style={
        "position": "absolute",
        "left": "0",
        "top": "8px",
        "bottom": "8px",
        "width": "6px",
        "background": accent_color,
        "opacity": 0.95,
        "borderRadius": "4px"
    })
    right_accent = html.Div(style={
        "position": "absolute",
        "right": "0",
        "top": "8px",
        "bottom": "8px",
        "width": "6px",
        "background": accent_color,
        "opacity": 0.95,
        "borderRadius": "4px"
    })
    label_style = {
        "fontSize": "clamp(10px, 1.2vw, 12px)",
        "opacity": 0.95,
        "textAlign": "left",
        "color": "white",
        "minWidth": "70px"
    }
    value_id = {'type':'net-metric','metric':metric,'index':index}
    unit_id = {'type':'net-unit','metric':metric,'index':index}
    label_id = {'type':'net-label','metric':metric,'index':index}
    fill_id = {'type':'net-bar-fill','metric':metric,'index':index}
    try:
        percent = (float(value) - float(min_val)) / (float(max_val) - float(min_val)) * 100.0
    except Exception:
        percent = 0.0
    content = html.Div([
        html.Div(label, id=label_id, style=label_style),
        html.Div(_value_with_unit(value_id, unit_id, f"{value}", unit),
                 style={"display":"flex","alignItems":"center","justifyContent":"center","minHeight":"44px"}),
        _packet_bar_container(fill_id, percent=percent, fill_color=accent_color)
    ], style={"display":"flex","flexDirection":"column","flex":"1","minWidth":"0","padding":"0 6px"})
    return html.Div([left_accent, right_accent, content], style=card_style)


def NetworkStatsRowCompact(index, metric, avg=None, min_val=None, max_val=None):
    value_style = {"fontSize":"12px","textAlign":"center","lineHeight":"14px","minWidth":"40px","color":"white"}
    label_style = {"fontSize":"10px","opacity":0.6,"textAlign":"center","color":"white"}
    return html.Div([
        html.Div([html.Div("AVG", style=label_style), html.Div(f"{avg}" if avg is not None else "-", id={'type':'net-stat-avg','metric':metric,'index':index}, style=value_style)]),
        html.Div([html.Div("MIN", style=label_style), html.Div(f"{min_val}" if min_val is not None else "-", id={'type':'net-stat-min','metric':metric,'index':index}, style=value_style)]),
        html.Div([html.Div("MAX", style=label_style), html.Div(f"{max_val}" if max_val is not None else "-", id={'type':'net-stat-max','metric':metric,'index':index}, style=value_style)])
    ], style={"display":"flex","flexDirection":"row","alignItems":"center","justifyContent":"space-around","marginTop":"6px","width":"100%","height":"36px","boxSizing":"border-box"})


def _separator_compact():
    return html.Div(style={
        "height": "1px",
        "backgroundColor": "rgba(255,255,255,0.03)",
        "margin": "8px 0",
        "width": "100%"
    })


def combinedNetworkPanel(index,
                         packet_loss=0.0,
                         delay_values=None,
                         connection_status="disconnected",
                         packet_stats=(None,None,None),
                         title="Netzwerk",
                         accent_color="#00aaff",
                         gap="10px"):
    header = html.Div(title, style={
        "height":"28px",
        "flex":"0 0 auto",
        "display":"flex",
        "alignItems":"center",
        "justifyContent":"center",
        "fontSize":"clamp(11px,1.4vw,13px)",
        "color":"white"
    })

    packet_block = html.Div([
        PacketLossMetricBlockCompact(index=index, metric="packet", label="Packet Loss", value=packet_loss, unit="%", min_val=0.0, max_val=100.0, accent_color=accent_color),
        NetworkStatsRowCompact(index=index, metric="packet", avg=packet_stats[0], min_val=packet_stats[1], max_val=packet_stats[2])
    ], style={"width":"100%"})

    spark_id = {'type':'net-spark','metric':'delay','index':index}
    delay_value_id = {'type':'net-delay-value','metric':'delay','index':index}
    delay_block = html.Div([
        html.Div("Delay", style={"fontSize":"12px","color":"white","opacity":0.9,"padding":"4px 8px","textAlign":"left"}),
        _delay_sparkline_graph_with_value(spark_id, delay_value_id, values=delay_values, stroke=accent_color, y_label="ms")
    ], style={"width":"100%","display":"flex","flexDirection":"column","minWidth":"0"})

    status_card = _status_card(status_id={'type':'net-status-lamp','metric':'conn','index':index},
                               text_id={'type':'net-status-text','metric':'conn','index':index},
                               detail_id={'type':'net-status-detail','metric':'conn','index':index},
                               initial_status=connection_status)

    metric_stack = html.Div([
        packet_block,
        _separator_compact(),
        delay_block,
        _separator_compact(),
        status_card
    ], style={"display":"flex","flexDirection":"column","gap": gap, "flex":"1 1 auto","minHeight":0,"overflow":"hidden","padding":"6px"})

    return html.Div([header, metric_stack], style={"display":"flex","flexDirection":"column","height":"100%","minHeight":0,"overflow":"hidden"})

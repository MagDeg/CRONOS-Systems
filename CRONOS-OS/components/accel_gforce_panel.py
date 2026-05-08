# components/accel_gforce_distance_power_style_compact_final.py
from dash import html, dcc
import plotly.graph_objects as go

def _gauge_figure_with_suffix(value, max_value, suffix,
                              bar_color="#ff7f50",
                              number_size=22, gauge_thickness=0.20, height=120):
    """
    Gauge helper sized to match compact_speed_drive_gauges_in_gauge_only.py:
    default height 120, number_size 22.
    """
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

def _value_with_unit(value_id, unit_id, value, unit):
    value_style = {
        "fontSize": "clamp(18px, 4.0vw, 34px)",
        "fontWeight": "700",
        "lineHeight": "1",
        "margin": "0",
        "padding": "0",
        "color": "white",
        "display": "inline-block",
        "verticalAlign": "middle"
    }
    unit_style = {
        "fontSize": "clamp(11px, 1.6vw, 16px)",
        "opacity": 0.95,
        "marginLeft": "8px",
        "display": "inline-block",
        "verticalAlign": "middle",
        "color": "white"
    }
    return html.Div([
        html.Span(value, id=value_id, style=value_style),
        html.Span(unit, id=unit_id, style=unit_style)
    ], style={"display":"flex","alignItems":"center","justifyContent":"center","gap":"8px","width":"100%"})

def _plain_power_style_block(index, metric, label, value=0, unit="", accent_color="#00d4ff", value_color="white",
                             padding_vertical="6px", inner_gap="10px", label_min_width="72px"):
    """
    Compact Power-style plain block (label + centered value+unit) with left/right accents.
    """
    card_style = {
        "backgroundColor": "rgba(255,255,255,0.02)",
        "borderRadius": "8px",
        "padding": f"{padding_vertical} 10px",
        "boxSizing": "border-box",
        "width": "100%",
        "display": "flex",
        "flexDirection": "row",
        "alignItems": "center",
        "gap": inner_gap,
        "position": "relative",
        "overflow": "hidden"
    }

    left_accent = html.Div(style={
        "position": "absolute",
        "left": "0",
        "top": "0",
        "bottom": "0",
        "width": "6px",
        "background": accent_color,
        "opacity": 0.95
    })
    right_accent = html.Div(style={
        "position": "absolute",
        "right": "0",
        "top": "0",
        "bottom": "0",
        "width": "6px",
        "background": accent_color,
        "opacity": 0.95
    })

    label_style = {
        "fontSize": "clamp(10px, 1.2vw, 12px)",
        "opacity": 0.95,
        "textAlign": "left",
        "color": "white",
        "minWidth": label_min_width
    }

    content = html.Div([
        html.Div(label, id={'type': f'{metric}-label', 'index': index}, style=label_style),
        html.Div(_value_with_unit({'type': f'{metric}-value', 'index': index},
                                  {'type': f'{metric}-unit', 'index': index},
                                  value, unit),
                 style={"flex":"1","display":"flex","alignItems":"center","justifyContent":"center","minHeight":"36px"})
    ], style={"display":"flex","flexDirection":"column","flex":"1","minWidth":"0","padding":"0 6px"})

    return html.Div([left_accent, right_accent, content], style=card_style)

def AccelGForceDistance(index,
                                              accel_value=0.0, accel_max=30.0,
                                              gforce_value=0.00, gforce_unit="g",
                                              distance_value=0.0, distance_unit="km",
                                              accel_color="#ff7f50", accent_color="#00d4ff",
                                              gauge_height=120, number_size=22,
                                              vertical_gap="6px",
                                              container_padding_top="4px"):
    """
    Final compact vertical panel:
      - Gauge sized like compact_speed_drive_gauges_in_gauge_only (height=120, number_size=22)
      - Two plain Power-style blocks underneath (G-Kräfte, Distanz)
      - Minimal top padding and small gaps between blocks
    IDs:
      - Gauge figure: {'type':'gauge','metric':'accel','index': index}
      - G-Force: {'type':'gforce-value'/'gforce-unit'/'gforce-label','index':index}
      - Distance: {'type':'distance-value'/'distance-unit'/'distance-label','index':index}
    """
    container_style = {
        "display": "flex",
        "flexDirection": "column",
        "height": "100%",
        "minHeight": 0,
        "overflow": "hidden",
        "boxSizing": "border-box",
        "gap": vertical_gap,
        "paddingTop": container_padding_top,
        "paddingRight": "8px",
        "paddingLeft": "8px",
        "paddingBottom": "8px",
        "color": "white"
    }

    header = html.Div("Beschleunigung · G‑Kräfte · Distanz", style={
        "height":"24px",
        "flex":"0 0 auto",
        "display":"flex",
        "alignItems":"center",
        "justifyContent":"center",
        "fontSize":"clamp(10px,1.2vw,12px)",
        "color":"white",
        "paddingTop":"0px",
        "paddingBottom":"2px",
        "margin":"0"
    })

    # Gauge (matches requested component size)
    accel_fig = _gauge_figure_with_suffix(accel_value, accel_max, " m/s²",
                                         bar_color=accel_color, number_size=number_size,
                                         gauge_thickness=0.20, height=gauge_height)
    accel_block = html.Div([
        html.Div("Beschleunigung", style={
            "fontSize":"clamp(10px, 1.0vw, 12px)",
            "opacity":0.95,
            "color":"white",
            "paddingBottom":"4px",
            "textAlign":"center",
            "width":"100%",
            "margin":"0"
        }),
        dcc.Graph(id={'type':'gauge','metric':'accel','index':index}, figure=accel_fig, config={"displayModeBar": False},
                  style={"width":"100%","height":f"{gauge_height}px","flex":"0 0 auto"})
    ], style={"display":"flex","flexDirection":"column","width":"100%","boxSizing":"border-box","margin":"0"})

    # Plain blocks (compact)
    gforce_block = _plain_power_style_block(index=index, metric="gforce", label="G‑Kräfte",
                                            value=f"{gforce_value:.2f}", unit=gforce_unit,
                                            accent_color=accent_color, value_color="white",
                                            padding_vertical="6px", inner_gap="10px", label_min_width="72px")

    distance_block = _plain_power_style_block(index=index, metric="distance", label="Distanz",
                                              value=f"{distance_value:.1f}", unit=distance_unit,
                                              accent_color=accent_color, value_color="white",
                                              padding_vertical="6px", inner_gap="10px", label_min_width="72px")

    return html.Div([header, accel_block, gforce_block, distance_block], style=container_style)

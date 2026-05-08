# components/power_panel_responsive.py
from dash import html

def _value_with_unit(value_id, unit_id, value, unit):
    """
    Inline Wert + Einheit, zentriert. Dynamische Schriftgrößen mit clamp().
    """
    value_style = {
        "fontSize": "clamp(20px, 4.5vw, 40px)",   # skaliert mit Panel/Bildschirm
        "fontWeight": "700",
        "lineHeight": "1",
        "margin": "0",
        "padding": "0",
        "color": "white",
        "display": "inline-block",
        "verticalAlign": "middle"
    }
    unit_style = {
        "fontSize": "clamp(12px, 1.8vw, 18px)",
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


def PowerMetricBlockResponsive(index, metric, label, value=0, unit="", accent_color="#00d4ff"):
    """
    Kompakter Block mit blauen Akzentstreifen links und rechts.
    Pattern IDs:
      - {'type':'power-metric','metric': metric, 'index': index}
      - {'type':'power-unit',  'metric': metric, 'index': index}
      - {'type':'power-label', 'metric': metric, 'index': index}
    """
    # Card style
    card_style = {
        "backgroundColor": "rgba(255,255,255,0.02)",
        "borderRadius": "8px",
        "padding": "6px 10px",
        "boxSizing": "border-box",
        "width": "100%",
        "display": "flex",
        "flexDirection": "row",
        "alignItems": "center",
        "gap": "10px",
        "position": "relative",
        "overflow": "hidden"
    }

    # left/right accent bars (absolute so they don't affect layout)
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

    # content column (label + value)
    label_style = {
        "fontSize": "clamp(11px, 1.6vw, 14px)",
        "opacity": 0.95,
        "textAlign": "left",
        "color": "white",
        "minWidth": "80px"
    }

    content = html.Div([
        html.Div(label, id={'type':'power-label','metric':metric,'index':index}, style=label_style),
        html.Div(_value_with_unit({'type':'power-metric','metric':metric,'index':index},
                                  {'type':'power-unit','metric':metric,'index':index},
                                  value, unit),
                 style={"flex":"1","display":"flex","alignItems":"center","justifyContent":"center","minHeight":"44px"})
    ], style={"display":"flex","flexDirection":"column","flex":"1","minWidth":"0","padding":"0 8px"})

    return html.Div([left_accent, right_accent, content], style=card_style)


def PowerStatsRowResponsive(index, metric, avg=None, min_val=None, max_val=None):
    """
    Kompakte Stats‑Zeile unter dem Block. Schriftgrößen dynamisch.
    Pattern IDs:
      - {'type':'stat-avg','metric':metric,'index':index}
      - {'type':'stat-min','metric':metric,'index':index}
      - {'type':'stat-max','metric':metric,'index':index}
    """
    value_style = {"fontSize":"clamp(11px,1.6vw,14px)","textAlign":"center","lineHeight":"16px","minWidth":"44px","color":"white"}
    label_style = {"fontSize":"clamp(9px,1.2vw,11px)","opacity":0.6,"textAlign":"center","color":"white"}

    return html.Div([
        html.Div([html.Div("AVG", style=label_style), html.Div(f"{avg}" if avg is not None else "-", id={'type':'stat-avg','metric':metric,'index':index}, style=value_style)]),
        html.Div([html.Div("MIN", style=label_style), html.Div(f"{min_val}" if min_val is not None else "-", id={'type':'stat-min','metric':metric,'index':index}, style=value_style)]),
        html.Div([html.Div("MAX", style=label_style), html.Div(f"{max_val}" if max_val is not None else "-", id={'type':'stat-max','metric':metric,'index':index}, style=value_style)])
    ], style={"display":"flex","flexDirection":"row","alignItems":"center","justifyContent":"space-around","marginTop":"6px","width":"100%","height":"40px","boxSizing":"border-box"})


def _separator_responsive():
    return html.Div(style={
        "height": "1px",
        "backgroundColor": "rgba(255,255,255,0.04)",
        "margin": "8px 0",
        "width": "100%"
    })


def combinedPowerPanel(index,
                                 voltage=0.0, voltage_unit="V", voltage_stats=(None,None,None),
                                 current=0.0, current_unit="A", current_stats=(None,None,None),
                                 power=0.0, power_unit="W", power_stats=(None,None,None),
                                 title="Elektrik",
                                 accent_color="#00d4ff"):
    """
    Responsive Panel: Header + für jede Metrik Block + Stats.
    Schriftgrößen und Abstände skalieren dynamisch mit clamp().
    """
    header = html.Div(title, style={"height": "30px", "flex": "0 0 auto", "display": "flex", "alignItems": "center", "justifyContent": "center"})

    voltage_block = html.Div([
        PowerMetricBlockResponsive(index=index, metric="voltage", label="Voltage", value=voltage, unit=voltage_unit, accent_color=accent_color),
        PowerStatsRowResponsive(index=index, metric="voltage", avg=voltage_stats[0], min_val=voltage_stats[1], max_val=voltage_stats[2])
    ], style={"width":"100%"})

    current_block = html.Div([
        PowerMetricBlockResponsive(index=index, metric="current", label="Current", value=current, unit=current_unit, accent_color=accent_color),
        PowerStatsRowResponsive(index=index, metric="current", avg=current_stats[0], min_val=current_stats[1], max_val=current_stats[2])
    ], style={"width":"100%"})

    power_block = html.Div([
        PowerMetricBlockResponsive(index=index, metric="power", label="Power", value=power, unit=power_unit, accent_color=accent_color),
        PowerStatsRowResponsive(index=index, metric="power", avg=power_stats[0], min_val=power_stats[1], max_val=power_stats[2])
    ], style={"width":"100%"})

    metric_stack = html.Div([
        voltage_block,
        _separator_responsive(),
        current_block,
        _separator_responsive(),
        power_block
    ], style={"display":"flex","flexDirection":"column","flex":"1 1 auto","minHeight":0,"overflow":"hidden","padding":"6px"})

    return html.Div([header, metric_stack], style={"display":"flex","flexDirection":"column","height":"100%","minHeight":0,"overflow":"hidden"})

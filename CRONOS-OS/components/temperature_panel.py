# components/temp_panel_bar_compact.py
from dash import html

def _value_with_unit_temp(value_id, unit_id, value, unit):
    value_style = {
        "fontSize": "clamp(18px, 3.5vw, 32px)",
        "fontWeight": "700",
        "lineHeight": "1",
        "margin": "0",
        "padding": "0",
        "color": "white",
        "display": "inline-block",
        "verticalAlign": "middle"
    }
    unit_style = {
        "fontSize": "clamp(11px, 1.4vw, 14px)",
        "opacity": 0.95,
        "marginLeft": "6px",
        "display": "inline-block",
        "verticalAlign": "middle",
        "color": "white"
    }
    return html.Div([
        html.Span(value, id=value_id, style=value_style),
        html.Span(unit, id=unit_id, style=unit_style)
    ], style={"display":"flex","alignItems":"center","justifyContent":"center","gap":"6px","width":"100%"})


def _temp_bar_container(fill_id, percent=0.0, fill_color="#00aaff"):
    """
    Kompakter Barcontainer mit innerem Fill-DIV, der per Callback über 'style' aktualisiert wird.
    Höhe reduziert, starke Abrundung.
    """
    container_style = {
        "width": "100%",
        "height": "8px",                       # kleinerer Balken
        "background": "rgba(255,255,255,0.03)",
        "borderRadius": "8px",                 # abgerundete Ecken
        "overflow": "hidden",
        "boxSizing": "border-box"
    }
    # initial fill style (width in %)
    fill_style = {
        "width": f"{max(0, min(100, float(percent)))}%",
        "height": "100%",
        "background": fill_color,
        "transition": "width 0.2s linear, background 0.2s linear",
        "borderRadius": "8px"
    }
    # outer wrapper includes padding so bar nicht direkt an Akzentstreifen klebt
    return html.Div([
        html.Div(style=container_style, children=[
            html.Div(id=fill_id, style=fill_style)
        ])
    ], style={"padding":"6px 8px","boxSizing":"border-box","width":"100%"})


def TempMetricBlockCompact(index, metric, label, value=0.0, unit="°C",
                           min_val=0.0, max_val=100.0, accent_color="#00aaff"):
    """
    Kompakter Block mit beidseitigen Akzentstreifen und kleinerem Bargraph.
    Pattern IDs:
      - {'type':'temp-metric','metric': metric,'index': index}
      - {'type':'temp-unit','metric': metric,'index': index}
      - {'type':'temp-label','metric': metric,'index': index}
      - {'type':'temp-bar-fill','metric': metric,'index': index}  -> style wird per Callback gesetzt
    """
    card_style = {
        "backgroundColor": "rgba(255,255,255,0.015)",
        "borderRadius": "10px",
        "padding": "6px 10px",
        "boxSizing": "border-box",
        "width": "100%",
        "display": "flex",
        "flexDirection": "column",
        "gap": "6px",
        "position": "relative",
        "overflow": "hidden"
    }

    left_accent = html.Div(style={
        "position": "absolute",
        "left": "0",
        "top": "6px",
        "bottom": "6px",
        "width": "6px",
        "background": accent_color,
        "opacity": 0.95,
        "borderRadius": "4px"
    })
    right_accent = html.Div(style={
        "position": "absolute",
        "right": "0",
        "top": "6px",
        "bottom": "6px",
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

    value_id = {'type':'temp-metric','metric':metric,'index':index}
    unit_id = {'type':'temp-unit','metric':metric,'index':index}
    label_id = {'type':'temp-label','metric':metric,'index':index}
    fill_id = {'type':'temp-bar-fill','metric':metric,'index':index}

    # compute initial percent safely
    try:
        percent = (float(value) - float(min_val)) / (float(max_val) - float(min_val)) * 100.0
    except Exception:
        percent = 0.0

    content = html.Div([
        html.Div(label, id=label_id, style=label_style),
        html.Div(_value_with_unit_temp(value_id, unit_id, f"{value}", unit),
                 style={"display":"flex","alignItems":"center","justifyContent":"center","minHeight":"36px"}),
        _temp_bar_container(fill_id, percent=percent, fill_color=accent_color)
    ], style={"display":"flex","flexDirection":"column","flex":"1","minWidth":"0","padding":"0 6px"})

    return html.Div([left_accent, right_accent, content], style=card_style)


def TempStatsRowCompact(index, metric, avg=None, min_val=None, max_val=None):
    value_style = {"fontSize":"12px","textAlign":"center","lineHeight":"14px","minWidth":"40px","color":"white"}
    label_style = {"fontSize":"10px","opacity":0.6,"textAlign":"center","color":"white"}

    return html.Div([
        html.Div([html.Div("AVG", style=label_style), html.Div(f"{avg}" if avg is not None else "-", id={'type':'stat-avg','metric':metric,'index':index}, style=value_style)]),
        html.Div([html.Div("MIN", style=label_style), html.Div(f"{min_val}" if min_val is not None else "-", id={'type':'stat-min','metric':metric,'index':index}, style=value_style)]),
        html.Div([html.Div("MAX", style=label_style), html.Div(f"{max_val}" if max_val is not None else "-", id={'type':'stat-max','metric':metric,'index':index}, style=value_style)])
    ], style={"display":"flex","flexDirection":"row","alignItems":"center","justifyContent":"space-around","marginTop":"6px","width":"100%","height":"36px","boxSizing":"border-box"})


def _separator_compact():
    return html.Div(style={
        "height": "1px",
        "backgroundColor": "rgba(255,255,255,0.03)",
        "margin": "6px 0",
        "width": "100%"
    })


def combinedTempPanel(index,
                                battery=25.0, chip=30.0, engine=60.0,
                                battery_stats=(None,None,None),
                                chip_stats=(None,None,None),
                                engine_stats=(None,None,None),
                                title="Temperaturen",
                                accent_color="#00aaff",
                                scale_min=0.0, scale_max=100.0):
    header = html.Div(title, style={
        "height":"28px",
        "flex":"0 0 auto",
        "display":"flex",
        "alignItems":"center",
        "justifyContent":"center",
        "fontSize":"clamp(11px,1.4vw,13px)",
        "color":"white"
    })

    battery_block = html.Div([
        TempMetricBlockCompact(index=index, metric="battery", label="Battery", value=battery, unit="°C", accent_color=accent_color, min_val=scale_min, max_val=scale_max),
        TempStatsRowCompact(index=index, metric="battery", avg=battery_stats[0], min_val=battery_stats[1], max_val=battery_stats[2])
    ], style={"width":"100%"})

    chip_block = html.Div([
        TempMetricBlockCompact(index=index, metric="chip", label="Chip", value=chip, unit="°C", accent_color=accent_color, min_val=scale_min, max_val=scale_max),
        TempStatsRowCompact(index=index, metric="chip", avg=chip_stats[0], min_val=chip_stats[1], max_val=chip_stats[2])
    ], style={"width":"100%"})

    engine_block = html.Div([
        TempMetricBlockCompact(index=index, metric="engine", label="Engine", value=engine, unit="°C", accent_color=accent_color, min_val=scale_min, max_val=scale_max),
        TempStatsRowCompact(index=index, metric="engine", avg=engine_stats[0], min_val=engine_stats[1], max_val=engine_stats[2])
    ], style={"width":"100%"})

    metric_stack = html.Div([
        battery_block,
        _separator_compact(),
        chip_block,
        _separator_compact(),
        engine_block
    ], style={"display":"flex","flexDirection":"column","flex":"1 1 auto","minHeight":0,"overflow":"hidden","padding":"4px"})

    return html.Div([header, metric_stack], style={"display":"flex","flexDirection":"column","height":"100%","minHeight":0,"overflow":"hidden"})

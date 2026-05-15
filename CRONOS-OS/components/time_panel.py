# components/time_panel_compact.py
from dash import html

def _value_block_with_accents(value_id, label, initial_value="-", accent_color="#00aaff"):
    """
    Einzelner Zeit-Block mit eigenen linken/rechten Akzentstreifen (unterbrochene Linien).
    """
    label_style = {
        "fontSize": "clamp(10px, 1.2vw, 12px)",
        "color": "white",
        "opacity": 0.9,
        "textAlign": "center",
        "marginBottom": "6px"
    }
    value_style = {
        "fontSize": "clamp(20px, 4.5vw, 36px)",
        "fontWeight": "700",
        "color": "white",
        "textAlign": "center",
        "lineHeight": "1"
    }

    # Block wrapper ist position:relative, damit die Akzente absolut innerhalb des Blocks sitzen
    block_style = {
        "display":"flex",
        "flexDirection":"column",
        "alignItems":"center",
        "justifyContent":"center",
        "padding":"8px 6px",
        "width":"100%",
        "boxSizing":"border-box",
        "position":"relative",
        "minHeight":"0"
    }

    left_accent = html.Div(style={
        "position":"absolute",
        "left":"0",
        "top":"8px",
        "bottom":"8px",
        "width":"6px",
        "background":accent_color,
        "opacity":0.95,
        "borderRadius":"4px"
    })
    right_accent = html.Div(style={
        "position":"absolute",
        "right":"0",
        "top":"8px",
        "bottom":"8px",
        "width":"6px",
        "background":accent_color,
        "opacity":0.95,
        "borderRadius":"4px"
    })

    return html.Div([
        left_accent,
        right_accent,
        html.Div(label, style=label_style),
        html.Div(initial_value, id=value_id, style=value_style)
    ], style=block_style)

def _separator():
    return html.Div(style={
        "height":"1px",
        "backgroundColor":"rgba(255,255,255,0.04)",
        "margin":"10px 0",
        "width":"100%"
    })

def TimePanel(index, title="Zeit", accent_color="#00aaff"):
    """
    Kompaktes Zeitpanel mit getrennten Seitenlinien pro Block.
    Pattern IDs:
      - {'type':'time-current','index': index}
      - {'type':'time-elapsed','index': index}
      - {'type':'time-remaining','index': index}
    """
    card_style = {
        "backgroundColor":"rgba(255,255,255,0.015)",
        "borderRadius":"10px",
        "padding":"8px 10px",
        "boxSizing":"border-box",
        "width":"100%",
        "height":"100%",
        "display":"flex",
        "flexDirection":"column",
        "overflow":"hidden",
        "position":"relative"
    }

    header = html.Div(title, style={
        "height":"32px",
        "display":"flex",
        "alignItems":"center",
        "justifyContent":"center",
        "fontSize":"clamp(11px,1.2vw,13px)",
        "color":"white",
        "fontWeight":"600",
        "paddingBottom":"4px"
    })

    # Pattern IDs
    current_id = {'type':'time-current','index':index}
    elapsed_id = {'type':'time-elapsed','index':index}
    remaining_id = {'type':'time-remaining','index':index}

    # Drei Blöcke, jeder mit eigenen Akzentstreifen (unterbrochen)
    body = html.Div([
        html.Div(_value_block_with_accents(current_id, "Aktuelle Zeit", "-", accent_color=accent_color),
                 style={"flex":"1 1 0","minHeight":"0"}),
        _separator(),
        html.Div(_value_block_with_accents(elapsed_id, "Verstrichene Zeit", "-", accent_color=accent_color),
                 style={"flex":"1 1 0","minHeight":"0"}),
        _separator(),
        html.Div(_value_block_with_accents(remaining_id, "Verbleibende Zeit", "-", accent_color=accent_color),
                 style={"flex":"1 1 0","minHeight":"0"})
    ], style={
        "display":"flex",
        "flexDirection":"column",
        "flex":"1 1 auto",
        "gap":"0px",
        "minHeight":"0",
        "justifyContent":"space-between",
        "padding":"4px 2px",
        "boxSizing":"border-box"
    })

    return html.Div([header, body], style=card_style)

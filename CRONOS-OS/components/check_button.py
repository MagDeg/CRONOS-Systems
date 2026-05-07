from dash import dcc, html

def create_switch(index: int, label: str, checked: bool = False):
    return html.Div(
        [
            dcc.Checklist(
                id={"type": "switch", "index": index},
                options=[{"label": "", "value": "on"}],
                value=["on"] if checked else []
            ),
            html.Span(label, style={"marginLeft": "8px"})
        ],
        style={"display": "flex", "alignItems": "center", "gap": "8px"}
    )
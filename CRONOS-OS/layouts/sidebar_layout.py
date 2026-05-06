from dash import html
from components.sidebar_panels import get_sidebar_panel


def get_right_sidebar_layout():
    return html.Div([
        get_sidebar_panel("Sth"),
        get_sidebar_panel("Tst"),
    ], className="sidebar")

def get_left_sidebar_layout():
    return html.Div([
        get_sidebar_panel("Lst"),
        get_sidebar_panel("Tst"),
    ], className="sidebar")
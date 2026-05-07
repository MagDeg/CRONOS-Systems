from dash import html
from components.sidebar_panels import get_sidebar_panel
from components.check_button import create_switch


def get_right_sidebar_layout():
    return html.Div([
        html.Div([
            create_switch(

                index=0,
                label="System Sound",
                checked=True
            ),

            create_switch(
                index=1,
                label="Alerts",
                checked=False
            )], className="sidebarPanel"),
        get_sidebar_panel("Tst"),
    ], className="sidebar")

def get_left_sidebar_layout():
    return html.Div([
        get_sidebar_panel("Lst"),
        get_sidebar_panel("Tst"),
    ], className="sidebar")
from dash import Output, Input, html

from layouts.main_view_layout import get_main_view_layout
from layouts.sidebar_layout import get_left_sidebar_layout, get_right_sidebar_layout

def register_routing_callbacks(app):
    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname")
    )
    def router(path):

        if path == "/panel1":
            return html.Div([
                get_left_sidebar_layout(),
                html.Div("SPEED PAGE", className="main"),
                get_right_sidebar_layout()
            ], className="content-container")



        # default = dashboard
        return get_main_view_layout()
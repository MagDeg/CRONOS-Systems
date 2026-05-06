from dash import Dash, html, dcc

from layouts.stats_layout import get_stats_layout
from layouts.topbar_layout import *
from layouts.bottombar_layout import *
from layouts.sidebar_layout import *

def get_main_layout():
    return html.Div([
        get_topbar_layout(),
        html.Div(id="page-content", className="content-container"),
        get_footer_layout(),
    ])
from dash import html

from layouts.sidebar_layout import get_right_sidebar_layout, get_left_sidebar_layout
from layouts.stats_layout import get_stats_layout


def get_main_view_layout():
    return html.Div([
        get_right_sidebar_layout(),
        get_stats_layout(),
        get_left_sidebar_layout(),
    ], className="content-container")
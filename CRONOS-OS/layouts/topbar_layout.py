from dash import html, dcc


def get_topbar_layout():
    return html.Div(
        dcc.Link(
            "C.R.O.N.O.S. | OS",
            href="/",
            style={
                "color": "#00bfff",
                "textDecoration": "none",
                "fontSize": "26px",
                "letterSpacing": "2px",
                "textTransform": "uppercase",
            },
            className="header-link"
        ),
        className="header"
    )
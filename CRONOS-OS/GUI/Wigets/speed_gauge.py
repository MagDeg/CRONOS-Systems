from dash import html, dcc
import plotly.graph_objects as go

# -----------------------------
# SpeedGauge Graph (nur Graph)
# -----------------------------
def SpeedGaugeGraph(value=120):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'font': {'size': 40}},
        title={'text': "km/h", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, 200], 'visible': False},
            'bar': {'color': "#00d4ff", 'thickness': 0.3},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [{'range': [0, 200], 'color': "#222"}],
        }
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "white"},
        margin=dict(l=0, r=0, t=0, b=0),
        height=None,
    )

    return dcc.Graph(
        id='speed-gauge-graph',
        figure=fig,
        config={"displayModeBar": False},
        style={
            "width": "100%",
            "height": "100%",
            "flex": "1"
        }
    )

# -----------------------------
# SpeedGauge Stats (unter Gauge)
# -----------------------------
def SpeedGaugeStats(avg=100, min_val=80, max_val=150):
    from dash import html

    value_style = {
        "fontSize": "20px",
        "textAlign": "center",
        "lineHeight": "24px",
        "minWidth": "40px"
    }

    label_style = {
        "fontSize": "12px",
        "opacity": 0.6,
        "textAlign": "center"
    }

    return html.Div([
        html.Div([
            html.Div("AVG", style=label_style),
            html.Div(f"{avg}", id="stat-avg", style=value_style)
        ]),
        html.Div([
            html.Div("MIN", style=label_style),
            html.Div(f"{min_val}", id="stat-min", style=value_style)
        ]),
        html.Div([
            html.Div("MAX", style=label_style),
            html.Div(f"{max_val}", id="stat-max", style=value_style)
        ])
    ], style={
        "display": "flex",
        "flexDirection": "row",
        "alignItems": "center",
        "justifyContent": "space-around",
        "marginTop": "4px",
        "width": "100%"
    })


# -----------------------------
# Kombinierte SpeedGauge (Graph + Stats)
# -----------------------------


def combinedSpeedGauge(value=120, avg=100, min_val=80, max_val=150):

    return html.Div([

        # HEADER (fix)
        html.Div(
            "Geschwindigkeit",
            style={
                "height": "30px",
                "flex": "0 0 auto",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            }
        ),

        # GAUGE (nimmt ALLES was übrig bleibt)
        html.Div(
            SpeedGaugeGraph(value=value),
            style={
                "flex": "1 1 auto",
                "minHeight": 0,
                "overflow": "hidden"
            }
        ),

        # STATS (fixe Zone unten)
        html.Div(
            SpeedGaugeStats(avg=avg, min_val=min_val, max_val=max_val),
            style={
                "height": "60px",
                "flex": "0 0 auto",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-around"
            }
        )

    ], style={
        "display": "flex",
        "flexDirection": "column",
        "height": "100%",
        "minHeight": 0,
        "overflow": "hidden"
    })
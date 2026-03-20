from dash import Dash, html, dcc

from GUI.components import Header, LeftSidebar, MainContent, RightSidebar, Footer

app = Dash(__name__)
app.title = "C.R.O.N.O.S. OS"

app.layout = html.Div([
    Header(),
    html.Div([
        LeftSidebar(),
        MainContent(),
        RightSidebar()
    ], className="content-container"),
    Footer(),
    dcc.Interval(
        id="gauge-update-interval",
        interval=500,  # Update alle 500ms
        n_intervals=0
    )
], className="app-container")

from dash import Output, Input


@app.callback(
    Output("speed-gauge-graph", "figure"),
    Output("stat-avg", "children"),
    Output("stat-min", "children"),
    Output("stat-max", "children"),
    Input("gauge-update-interval", "n_intervals")
)
def update_speed(n):
    import random
    import plotly.graph_objects as go

    # Dynamische Werte
    new_value = 80 + 70 * random.random()
    avg_val = 90 + 20 * random.random()
    min_val = 60 + 10 * random.random()
    max_val = 160 + 20 * random.random()

    # Update Graph
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=new_value,
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
        autosize=True,
        transition={'duration': 250, 'easing': 'cubic-in-out'}
    )

    return fig, f"{avg_val:.1f}", f"{min_val:.1f}", f"{max_val:.1f}"

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
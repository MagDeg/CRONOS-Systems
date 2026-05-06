
from callbacks.register_callbacks import register_callbacks
from layouts.main_layout import *


app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "C.R.O.N.O.S. OS"

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    get_main_layout(),
    dcc.Interval(
        id="gauge-update-interval",
        interval=500,  # Update alle 500ms
        n_intervals=0
    )
], className="app-container")


register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
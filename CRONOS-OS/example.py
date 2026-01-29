# example.py
import threading
import time
import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output, State, dash, callback_context
import plotly.express as px

# ------------------------------
# DATENPUFFER UND STATUS
# ------------------------------
data_buffer = pd.DataFrame({'Zeit': [], 'Wert': []})
reading_active = False
filter_value = 0.0
selected_port = None
log_messages = []

# ------------------------------
# SERIELLE DATEN / SIMULATION
# ------------------------------
def read_serial():
    global data_buffer, reading_active, log_messages
    while True:
        if reading_active:
            time.sleep(1)
            timestamp = pd.Timestamp.now()
            value = np.random.randn() * 10 + 50  # Simulierte Werte
            data_buffer = pd.concat([data_buffer, pd.DataFrame({'Zeit':[timestamp],'Wert':[value]})])
            if len(data_buffer) > 1000:
                data_buffer = data_buffer.iloc[-1000:]
            # Log Message
            log_messages.append(f"{timestamp}: Neuer Wert = {value:.2f}")
            if len(log_messages) > 50:
                log_messages = log_messages[-50:]
        else:
            time.sleep(0.1)

threading.Thread(target=read_serial, daemon=True).start()

# ------------------------------
# DASH APP
# ------------------------------
app = Dash(__name__)
app.title = "Demo Serial Dashboard"

app.layout = html.Div([
    html.H1("Demo Dashboard für serielle Daten"),

    html.Div([
        html.Label("Serielle Schnittstelle:"),
        dcc.Dropdown(
            id='port-dropdown',
            options=[
                {'label': 'COM3', 'value': 'COM3'},
                {'label': '/dev/ttyUSB0', 'value': '/dev/ttyUSB0'}
            ],
            value=None
        ),
        html.Button("Start", id='start-button', n_clicks=0),
        html.Button("Stop", id='stop-button', n_clicks=0),
        html.Button("Reset", id='reset-button', n_clicks=0),
    ], style={'margin-bottom':'20px'}),

    html.Div([
        html.Label("Filterwert:"),
        dcc.Input(id='filter-input', type='number', value=0),
    ], style={'margin-bottom':'20px'}),

    dcc.Graph(id='live-graph'),

    html.Div(id='stats-output', style={'margin-top':'20px', 'font-size':'16px'}),

    html.H3("Terminal / Logs"),
    html.Div(id='log-output', style={
        'backgroundColor':'#f0f0f0','height':'200px','overflowY':'scroll',
        'padding':'10px','border':'1px solid #ccc'
    }),

    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
])

# ------------------------------
# CALLBACKS
# ------------------------------
@app.callback(
    Output('live-graph', 'figure'),
    Output('stats-output', 'children'),
    Output('log-output', 'children'),
    Input('start-button', 'n_clicks'),
    Input('stop-button', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    Input('port-dropdown', 'value'),
    Input('filter-input', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_dashboard(start_clicks, stop_clicks, reset_clicks, port, filter_input, n_intervals):
    global reading_active, selected_port, filter_value, data_buffer, log_messages

    ctx = callback_context
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    else:
        button_id = None

    # Buttons Aktionen
    if button_id == 'start-button':
        reading_active = True
        selected_port = port
        log_messages.append("Start gedrückt!")
    elif button_id == 'stop-button':
        reading_active = False
        log_messages.append("Stop gedrückt!")
    elif button_id == 'reset-button':
        data_buffer = pd.DataFrame({'Zeit': [], 'Wert': []})
        log_messages.append("Daten zurückgesetzt!")

    # Filterwert
    if filter_input is not None:
        filter_value = filter_input

    # Daten anwenden
    if filter_value != 0:
        filtered_data = data_buffer[data_buffer['Wert'] >= filter_value]
    else:
        filtered_data = data_buffer.copy()

    # Graph erstellen
    if len(filtered_data) > 0:
        fig = px.line(filtered_data, x='Zeit', y='Wert', title='Serielle Daten Live')
    else:
        fig = px.line(title='Serielle Daten Live')

    # Statistik
    if len(filtered_data) > 0:
        mean = filtered_data['Wert'].mean()
        std = filtered_data['Wert'].std()
        min_val = filtered_data['Wert'].min()
        max_val = filtered_data['Wert'].max()
        stats_text = f"Mittelwert: {mean:.2f}, Std: {std:.2f}, Min: {min_val:.2f}, Max: {max_val:.2f}"
    else:
        stats_text = "Keine Daten verfügbar"

    # Log Output (nur letzten 50 Einträge)
    log_text = "\n".join(log_messages[-50:])

    return fig, stats_text, log_text

# ------------------------------
# SERVER START
# ------------------------------
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8050, debug=True)

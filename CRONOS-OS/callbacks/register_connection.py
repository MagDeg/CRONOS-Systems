# callbacks/network_panel_callbacks.py
import time
import random
from collections import deque
from dash import Input, Output, MATCH
import dash
import plotly.graph_objs as go

# history: { index: { 'packet': deque, 'delay': deque } }
_history = {}

def _ensure_history(index, maxlen=5000):
    if index not in _history:
        _history[index] = {
            'packet': deque(maxlen=maxlen),
            'delay':  deque(maxlen=maxlen)
        }

def _push_random_network_sample(index):
    """
    Erzeugt einen zufälligen Sample-Dict und speichert Timestamped-Werte in _history.
    Rückgabe: {'ts': float, 'packet': float, 'delay': int}
    """
    ts = time.time()
    # Packet loss in percent (simulate occasional spikes)
    packet = round(max(0.0, random.gauss(1.5, 2.0)), 2)
    # Delay in ms (simulate jitter)
    delay = int(max(1, random.gauss(12, 6)))
    _ensure_history(index)
    _history[index]['packet'].append((ts, float(packet)))
    _history[index]['delay'].append((ts, int(delay)))
    return {'ts': ts, 'packet': packet, 'delay': delay}

def _trim_window(index, metric, window_seconds):
    _ensure_history(index)
    now = time.time()
    dq = _history[index][metric]
    while dq and (now - dq[0][0]) > window_seconds:
        dq.popleft()

def _calc_stats(index, metric, window_seconds):
    """
    Liefert (avg, min, max) als formatierte Strings oder (None,None,None) wenn keine Daten.
    """
    _ensure_history(index)
    _trim_window(index, metric, window_seconds)
    dq = _history[index][metric]
    if not dq:
        return (None, None, None)
    vals = [v for (_, v) in dq]
    avg = sum(vals) / len(vals)
    mn = min(vals)
    mx = max(vals)
    # Formatierung: Packet Loss with 2 decimals, Delay as integer
    if metric == 'packet':
        return (f"{avg:.2f}", f"{mn:.2f}", f"{mx:.2f}")
    else:
        return (f"{avg:.0f}", f"{mn:.0f}", f"{mx:.0f}")

def _value_to_percent(value, min_val, max_val):
    try:
        v = float(value)
        p = (v - float(min_val)) / (float(max_val) - float(min_val)) * 100.0
        return max(0.0, min(100.0, p))
    except Exception:
        return 0.0

def _color_for_packet_loss(packet_loss):
    """
    Farbwahl basierend auf Packet Loss (in %):
      <=1% green, <=3% yellow, >3% red
    """
    try:
        p = float(packet_loss)
    except Exception:
        p = 0.0
    if p <= 1.0:
        return "#2ecc71"
    if p <= 3.0:
        return "#ffb020"
    return "#ff4d4f"

def _make_delay_figure(values, stroke="#00aaff"):
    """
    Erzeugt eine kleine Plotly-Figur für die Sparkline. Y-Achsentitel wird kompatibel gesetzt.
    """
    fig = go.Figure(go.Scatter(
        x=list(range(len(values))),
        y=values,
        mode="lines",
        line=dict(color=stroke, width=2),
        hoverinfo="y"
    ))
    fig.update_layout(
        margin=dict(l=6, r=6, t=4, b=4),
        xaxis=dict(visible=False),
        yaxis=dict(
            visible=True,
            title=dict(text="ms", font=dict(size=10, color="#ffffff")),
            tickfont=dict(size=10, color="#cccccc")
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=56
    )
    return fig

def register_network_callbacks(app, window_seconds=10.0, scale_min=0.0, scale_max=100.0):
    """
    Registriert einen Callback, der für jedes Panel (MATCH) die folgenden Outputs liefert:
      1) {'type':'net-metric','metric':'packet','index': MATCH}.children
      2) {'type':'net-unit','metric':'packet','index': MATCH}.children
      3) {'type':'net-stat-avg','metric':'packet','index': MATCH}.children
      4) {'type':'net-stat-min','metric':'packet','index': MATCH}.children
      5) {'type':'net-stat-max','metric':'packet','index': MATCH}.children
      6) {'type':'net-bar-fill','metric':'packet','index': MATCH}.style
      7) {'type':'net-spark','metric':'delay','index': MATCH}.figure
      8) {'type':'net-delay-value','metric':'delay','index': MATCH}.children
      9) {'type':'net-status-lamp','metric':'conn','index': MATCH}.style
     10) {'type':'net-status-text','metric':'conn','index': MATCH}.children
     11) {'type':'net-status-detail','metric':'conn','index': MATCH}.children
    Inputs:
      - 'gauge-update-interval'.n_intervals
      - {'type':'panel-config','index': MATCH}.data
    """
    @app.callback(
        Output({'type':'net-metric','metric':'packet','index': MATCH}, 'children'),
        Output({'type':'net-unit','metric':'packet','index': MATCH}, 'children'),
        Output({'type':'net-stat-avg','metric':'packet','index': MATCH}, 'children'),
        Output({'type':'net-stat-min','metric':'packet','index': MATCH}, 'children'),
        Output({'type':'net-stat-max','metric':'packet','index': MATCH}, 'children'),
        Output({'type':'net-bar-fill','metric':'packet','index': MATCH}, 'style'),
        Output({'type':'net-spark','metric':'delay','index': MATCH}, 'figure'),
        Output({'type':'net-delay-value','metric':'delay','index': MATCH}, 'children'),
        Output({'type':'net-status-lamp','metric':'conn','index': MATCH}, 'style'),
        Output({'type':'net-status-text','metric':'conn','index': MATCH}, 'children'),
        Output({'type':'net-status-detail','metric':'conn','index': MATCH}, 'children'),
        Input('gauge-update-interval', 'n_intervals'),
        Input({'type':'panel-config','index': MATCH}, 'data'),
        prevent_initial_call=False
    )
    def _update_network(n_intervals, panel_config):
        # Wenn panel_config fehlt, gib no_update zurück (keine Änderung)
        if not panel_config:
            return (dash.no_update,)*11

        idx = panel_config.get('index')
        if idx is None:
            return (dash.no_update,)*11

        try:
            # --- Erzeuge und speichere zufällige Messwerte ---
            sample = _push_random_network_sample(idx)
            packet_val = sample.get('packet')
            delay_val = sample.get('delay')

            # --- Statistik (window) für Packet Loss ---
            avg_p, min_p, max_p = _calc_stats(idx, 'packet', window_seconds)
            avg_p = avg_p if avg_p is not None else "-"
            min_p = min_p if min_p is not None else "-"
            max_p = max_p if max_p is not None else "-"

            # --- Füllbalken für Packet Loss ---
            percent = _value_to_percent(packet_val, scale_min, scale_max)
            color = _color_for_packet_loss(packet_val)
            fill_style = {
                "width": f"{percent:.1f}%",
                "height": "100%",
                "background": color,
                "transition": "width 0.18s linear, background 0.18s linear",
                "borderRadius": "8px"
            }

            # --- Delay Sparkline (verwende die letzten N Werte aus history) ---
            _trim_window(idx, 'delay', window_seconds)  # optional trim
            delay_deque = _history[idx]['delay']
            delay_values = [v for (_, v) in delay_deque] if delay_deque else [delay_val]
            # Falls history noch kurz ist, fülle mit aktuellen Wert
            if len(delay_values) < 6:
                delay_values = (delay_values + [delay_val]*6)[:10]
            fig = _make_delay_figure(delay_values, stroke=panel_config.get('accent_color', "#00aaff"))

            # --- Delay absolute value (aktueller Messwert) ---
            delay_text = f"{delay_val} ms" if delay_val is not None else "-"

            # --- Verbindungsstatus (einfaches Heuristik-Beispiel) ---
            if packet_val is None:
                status_text = "Disconnected"
                lamp_color = "#ff4d4f"
            else:
                if packet_val > 20 or random.random() < 0.02:
                    status_text = "Disconnected"
                    lamp_color = "#ff4d4f"
                elif packet_val > 5:
                    status_text = "Degraded"
                    lamp_color = "#ffb020"
                else:
                    status_text = "Connected"
                    lamp_color = "#2ecc71"

            lamp_style = {
                "width":"14px",
                "height":"14px",
                "borderRadius":"50%",
                "background": lamp_color,
                "boxShadow":"0 0 8px rgba(0,0,0,0.45)",
                "display":"inline-block",
                "verticalAlign":"middle"
            }

            # --- Detailkachel: nur "Letzte Prüfung" (UTC) ---
            last_checked = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(sample['ts'])) + " UTC"
            detail_children = [dash.html.Div(f"Letzte Prüfung: {last_checked}")]

            # Rückgabe in exakt dieser Reihenfolge (11 Werte)
            return (
                f"{packet_val}",        # net-metric.children
                "%",                    # net-unit.children
                f"{avg_p}",             # net-stat-avg.children
                f"{min_p}",             # net-stat-min.children
                f"{max_p}",             # net-stat-max.children
                fill_style,             # net-bar-fill.style
                fig,                    # net-spark.figure
                delay_text,             # net-delay-value.children
                lamp_style,             # net-status-lamp.style
                status_text,            # net-status-text.children
                detail_children         # net-status-detail.children
            )

        except Exception as e:
            print(f"[network-callback] Fehler für panel={idx}: {e}")
            return (dash.no_update,)*11

    # End of register function
    return _update_network

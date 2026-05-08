# callbacks/temp_panel_bar_compact_callbacks_fixed_no_accents.py
import time
import random
from collections import deque
from dash import Input, Output, MATCH
import dash

_history = {}  # { index: { 'battery': deque, 'chip': deque, 'engine': deque } }

def _ensure_history(index):
    if index not in _history:
        _history[index] = {
            'battery': deque(maxlen=5000),
            'chip':    deque(maxlen=5000),
            'engine':  deque(maxlen=5000)
        }

def _push_random_temp(index):
    ts = time.time()
    sample = {
        'ts': ts,
        'battery': round(random.uniform(15.0, 45.0), 1),
        'chip':    round(random.uniform(20.0, 80.0), 1),
        'engine':  round(random.uniform(30.0, 100.0), 1)
    }
    _ensure_history(index)
    for m in ('battery','chip','engine'):
        _history[index][m].append((ts, float(sample[m])))
    return sample

def _calc_stats(index, metric, window_seconds):
    _ensure_history(index)
    now = time.time()
    dq = _history[index][metric]
    while dq and (now - dq[0][0]) > window_seconds:
        dq.popleft()
    if not dq:
        return (None, None, None)
    vals = [v for (_, v) in dq]
    avg = sum(vals) / len(vals)
    mn = min(vals)
    mx = max(vals)
    return (f"{avg:.1f}", f"{mn:.1f}", f"{mx:.1f}")

def _value_to_percent(value, min_val, max_val):
    try:
        v = float(value)
        p = (v - float(min_val)) / (float(max_val) - float(min_val)) * 100.0
        return max(0.0, min(100.0, p))
    except Exception:
        return 0.0

def _color_for_percent(percent):
    p = max(0.0, min(100.0, float(percent))) / 100.0
    r = int(p * 255 + (1 - p) * 0)
    g = int(p * 165 + (1 - p) * 170)
    b = int(p * 80  + (1 - p) * 255)
    return f"rgb({r},{g},{b})"

def register_temperature_callbacks(app, window_seconds=10.0, scale_min=0.0, scale_max=100.0):
    """
    Outputs (in dieser Reihenfolge):
      1) temp-metric.children
      2) temp-unit.children
      3) stat-avg.children
      4) stat-min.children
      5) stat-max.children
      6) temp-bar-fill.style
    Keine Outputs für temp-accent-left/right mehr.
    """

    def _make_callback(metric, unit_default="°C"):
        @app.callback(
            Output({'type':'temp-metric','metric': metric,'index': MATCH}, 'children'),
            Output({'type':'temp-unit','metric': metric,'index': MATCH}, 'children'),
            Output({'type':'stat-avg','metric': metric,'index': MATCH}, 'children'),
            Output({'type':'stat-min','metric': metric,'index': MATCH}, 'children'),
            Output({'type':'stat-max','metric': metric,'index': MATCH}, 'children'),
            Output({'type':'temp-bar-fill','metric': metric,'index': MATCH}, 'style'),
            Input('gauge-update-interval', 'n_intervals'),
            Input({'type':'panel-config','index': MATCH}, 'data'),
            prevent_initial_call=False
        )
        def _update_temp(n_intervals, panel_config):
            # Wenn panel_config fehlt, gib no_update für alle Outputs zurück
            if not panel_config:
                return (dash.no_update,)*6

            idx = panel_config.get('index')
            if idx is None:
                return (dash.no_update,)*6

            try:
                sample = _push_random_temp(idx)
                raw_val = sample.get(metric)
                display_val = f"{raw_val:.1f}" if raw_val is not None else "-"
                unit = unit_default

                avg, mn, mx = _calc_stats(idx, metric, window_seconds)
                avg = avg if avg is not None else "-"
                mn  = mn  if mn  is not None else "-"
                mx  = mx  if mx  is not None else "-"

                percent = _value_to_percent(raw_val, scale_min, scale_max)
                color = _color_for_percent(percent)

                fill_style = {
                    "width": f"{percent:.1f}%",
                    "height": "100%",
                    "background": color,
                    "transition": "width 0.18s linear, background 0.18s linear",
                    "borderRadius": "8px"
                }

                return display_val, unit, avg, mn, mx, fill_style

            except Exception as e:
                print(f"[temp-callback] Fehler für metric={metric}, panel={idx}: {e}")
                return (dash.no_update,)*6

        return _update_temp

    _make_callback('battery')
    _make_callback('chip')
    _make_callback('engine')

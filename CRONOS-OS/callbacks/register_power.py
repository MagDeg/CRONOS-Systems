# callbacks/power_panel_test_callbacks.py
import time
import random
from collections import deque
from dash import Input, Output, MATCH
import dash

# In-memory history buffers for stats (per index and metric)
_history = {}  # { index: { 'voltage': deque, 'current': deque, 'power': deque } }

def _ensure_history(index):
    if index not in _history:
        _history[index] = {
            'voltage': deque(maxlen=5000),
            'current': deque(maxlen=5000),
            'power':   deque(maxlen=5000)
        }

def _push_random_sample_into_history(index):
    """
    Generate a random sample for testing and append to history.
    Voltage ~ 11.0..13.0 V, Current ~ 0..10 A, Power ~ 0..200 W
    """
    ts = time.time()
    sample = {
        'ts': ts,
        'voltage': round(random.uniform(11.0, 13.0), 2),
        'current': round(random.uniform(0.0, 10.0), 2),
        'power':   round(random.uniform(0.0, 200.0), 1)
    }
    _ensure_history(index)
    for m in ('voltage', 'current', 'power'):
        _history[index][m].append((ts, float(sample[m])))
    return sample

def _calc_stats_from_history(index, metric, window_seconds):
    """
    Compute (avg, min, max) over the last window_seconds from the history deque.
    Returns formatted strings or (None, None, None) if no data.
    """
    _ensure_history(index)
    now = time.time()
    dq = _history[index][metric]
    # drop old entries
    while dq and (now - dq[0][0]) > window_seconds:
        dq.popleft()
    if not dq:
        return (None, None, None)
    vals = [v for (_, v) in dq]
    avg = sum(vals) / len(vals)
    mn = min(vals)
    mx = max(vals)
    # formatting per metric
    if metric == 'power':
        fmt = lambda x: f"{x:.1f}"
    else:
        fmt = lambda x: f"{x:.2f}"
    return (fmt(avg), fmt(mn), fmt(mx))

def register_power_callbacks(app, window_seconds=10.0):
    """
    Register MATCH callbacks that inject random test values for voltage/current/power.
    Use this during development/testing. Each callback:
      - generates a random sample for the panel index
      - appends it to the per-index history
      - returns display value, unit and AVG/MIN/MAX over window_seconds

    Call once during app setup: register_power_callbacks(app)
    """

    def _make_callback(metric, unit_default):
        @app.callback(
            Output({'type':'power-metric','metric': metric,'index': MATCH}, 'children'),
            Output({'type':'power-unit','metric': metric,'index': MATCH}, 'children'),
            Output({'type':'stat-avg','metric': metric,'index': MATCH}, 'children'),
            Output({'type':'stat-min','metric': metric,'index': MATCH}, 'children'),
            Output({'type':'stat-max','metric': metric,'index': MATCH}, 'children'),
            Input('gauge-update-interval', 'n_intervals'),
            Input({'type':'panel-config','index': MATCH}, 'data'),
            prevent_initial_call=False
        )
        def _update_metric(n_intervals, panel_config):
            # If panel_config missing, we cannot determine index for MATCH; return placeholders
            if not panel_config:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            idx = panel_config.get('index')
            if idx is None:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            # Generate a random sample for testing and push into history
            sample = _push_random_sample_into_history(idx)

            raw_val = sample.get(metric)
            if raw_val is None:
                display_val = "-"
            else:
                if metric == 'power':
                    display_val = f"{raw_val:.1f}"
                else:
                    display_val = f"{raw_val:.2f}"

            unit = unit_default

            # compute stats from history
            avg, mn, mx = _calc_stats_from_history(idx, metric, window_seconds=window_seconds)
            avg = avg if avg is not None else "-"
            mn  = mn  if mn  is not None else "-"
            mx  = mx  if mx  is not None else "-"

            return display_val, unit, avg, mn, mx

        return _update_metric

    # register callbacks for each metric
    _make_callback('voltage', 'V')
    _make_callback('current', 'A')
    _make_callback('power', 'W')

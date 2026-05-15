# callbacks/time_panel_compact_callbacks.py
import time
import random
from datetime import datetime, timezone
from dash import Input, Output, MATCH
import dash
from dateutil import parser as dateparser  # pip install python-dateutil if needed

def _parse_ts(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        try:
            dt = dateparser.parse(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            return None

def _format_hms(seconds):
    if seconds is None:
        return "-"
    try:
        s = int(round(seconds))
        if s < 0:
            return "0:00"
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        if h > 0:
            return f"{h:d}:{m:02d}:{sec:02d}"
        else:
            return f"{m:d}:{sec:02d}"
    except Exception:
        return "-"

def register_time_panel_compact_callbacks(app):
    @app.callback(
        Output({'type':'time-current','index': MATCH}, 'children'),
        Output({'type':'time-elapsed','index': MATCH}, 'children'),
        Output({'type':'time-remaining','index': MATCH}, 'children'),
        Input('gauge-update-interval', 'n_intervals'),
        Input({'type':'panel-config','index': MATCH}, 'data'),
        prevent_initial_call=False
    )
    def _update_time_compact(n_intervals, panel_config):
        try:
            now_ts = time.time()

            if not panel_config:
                start_ts = now_ts - random.randint(0, 3600)
                target_ts = now_ts + random.randint(60, 7200)
                tz = "local"
            else:
                tz = panel_config.get('timezone', 'local')
                start_ts = _parse_ts(panel_config.get('start_ts'))
                target_ts = _parse_ts(panel_config.get('target_ts'))
                if start_ts is None and target_ts is None:
                    start_ts = now_ts - random.randint(0, 3600)
                    target_ts = now_ts + random.randint(60, 7200)
                elif start_ts is None and target_ts is not None:
                    start_ts = target_ts - 3600
                elif target_ts is None and start_ts is not None:
                    target_ts = start_ts + 3600

            # Nur Uhrzeit anzeigen (kein Datum)
            if tz == "utc":
                current_str = datetime.utcfromtimestamp(now_ts).strftime("%H:%M:%S UTC")
            else:
                current_str = datetime.fromtimestamp(now_ts).strftime("%H:%M:%S")

            elapsed_seconds = now_ts - start_ts if start_ts is not None else None
            elapsed_str = _format_hms(elapsed_seconds)

            remaining_seconds = target_ts - now_ts if target_ts is not None else None
            remaining_str = _format_hms(remaining_seconds)

            return current_str, elapsed_str, remaining_str

        except Exception as e:
            print(f"[time-compact-callback] Fehler: {e}")
            return (dash.no_update, dash.no_update, dash.no_update)

    return _update_time_compact

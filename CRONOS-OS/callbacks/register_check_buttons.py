from dash import Input, Output, callback_context, MATCH
import json

def register_buttons(app):
    # MATCH-Callback: ruft per match/case den passenden Task auf und gibt den neuen Zustand zurück
    @app.callback(
        Output("status", "children"),
        Input({"type": "switch", "index": MATCH}, "value")
    )
    def on_switch_change(value):
        # neuer Zustand (bool)
        is_on = bool(value)

        # Index der ausgelösten Komponente ermitteln
        prop = callback_context.triggered[0]["prop_id"]  # z.B. '{"type":"switch","index":2}.value'
        idx = None
        try:
            idx = json.loads(prop.split(".")[0]).get("index")
        except Exception:
            pass

        # match / case (Python 3.10+)
        match idx:
            case 0:
                pass
            case 1:
                pass
            case 2:
                pass
            case _:
                pass

        # Rückgabe: neuer Zustand unverändert (nur als Anzeige)
        return "AN" if is_on else "AUS"
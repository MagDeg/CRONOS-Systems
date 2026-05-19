#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# C.R.O.N.O.S. OS — quickstart script
#   Activates the virtual environment (if present), installs any missing
#   dependencies, and launches the dashboard.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Detect virtual environment (respect an already-active venv, then check .venv)
if [ -z "${VIRTUAL_ENV:-}" ]; then
    if [ -d ".venv" ]; then
        # shellcheck disable=SC1091
        source .venv/bin/activate
    fi
fi

# Ensure PySide6 and pyserial are installed
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "[SETUP] Installing PySide6 + pyserial..."
    pip install --quiet PySide6 pyserial
fi

echo "[LAUNCH] C.R.O.N.O.S. OS dashboard"
exec python3 main.py "$@"

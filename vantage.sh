#!/usr/bin/env bash
# ==============================================================================
# Lenovo Vantage Pro — Application Entrypoint
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/src/app.py" ]; then
    exec python3 "$SCRIPT_DIR/src/app.py" "$@"
elif [ -f "/opt/lenovo-vantage/app.py" ]; then
    exec python3 "/opt/lenovo-vantage/app.py" "$@"
else
    echo "Error: Lenovo Vantage Pro source not found."
    exit 1
fi

#!/usr/bin/env sh
# ✈ 飞行足迹 · Flight Footprints — start the local server (macOS / Linux)
#
# Why a server at all?  Browsers refuse to let a page opened straight from disk
# (file://) read airports.csv / sample.csv, so search and the sample data would
# silently do nothing. Any static server works; this one needs only Python 3.
#
# It binds to 127.0.0.1 on purpose — your flight log stays on this machine,
# which is the whole point of the app. To reach it from your phone on the same
# Wi-Fi, run:  python3 -m http.server 8000 --bind 0.0.0.0   (and mind who else
# is on that network).
set -e
cd "$(dirname "$0")"

PORT="${1:-8000}"

PY=""
for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
    echo "✗ Python 3 not found." >&2
    echo "  Install it, or serve this folder with any static file server." >&2
    exit 1
fi

URL="http://localhost:$PORT"
echo "========================================"
echo "  ✈ 飞行足迹 · Flight Footprints"
echo "========================================"
echo "  → $URL   (Ctrl+C to stop)"
echo

# Best-effort: open the browser a moment after the server is up.
(
    sleep 1
    if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1
    elif command -v open >/dev/null 2>&1; then open "$URL" >/dev/null 2>&1
    fi
) >/dev/null 2>&1 &

exec "$PY" -m http.server "$PORT" --bind 127.0.0.1

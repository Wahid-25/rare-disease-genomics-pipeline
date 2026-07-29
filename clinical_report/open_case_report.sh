#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
    cat <<'USAGE'
Usage:
  bash clinical_report/open_case_report.sh CASE_ID [--port PORT]

Example:
  bash clinical_report/open_case_report.sh example_case

Purpose:
  Starts a local-only web server and opens the selected case's
  clinical-report JSON automatically in the report builder.
USAGE
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

CASE_ID="$1"
shift

PORT="8765"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)
            [[ $# -ge 2 ]] || die "--port requires a value."
            PORT="$2"
            shift 2
            ;;

        -h|--help)
            usage
            exit 0
            ;;

        *)
            die "Unknown option: $1"
            ;;
    esac
done

[[ "$CASE_ID" =~ ^[A-Za-z0-9._-]+$ ]] \
    || die "Unsafe case ID."

[[ "$PORT" =~ ^[0-9]+$ ]] \
    || die "Port must be numeric."

(( PORT >= 1024 && PORT <= 65535 )) \
    || die "Port must be between 1024 and 65535."

SCRIPT_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")" &&
    pwd
)"

PROJECT_ROOT="$(
    cd "$SCRIPT_DIR/.." &&
    pwd
)"

REPORT_HTML="$PROJECT_ROOT/clinical_report/index.html"

REPORT_JSON="$PROJECT_ROOT/results/cases/$CASE_ID/final/report/${CASE_ID}.report_draft.json"

CHECKSUM_FILE="${REPORT_JSON}.sha256"

[[ -s "$REPORT_HTML" ]] \
    || die "Report builder is missing: $REPORT_HTML"

[[ -s "$REPORT_JSON" ]] \
    || die "Draft report JSON is missing: $REPORT_JSON"

python3 -m json.tool \
    "$REPORT_JSON" \
    >/dev/null \
    || die "Draft report JSON is invalid."

if [[ -s "$CHECKSUM_FILE" ]]; then
    (
        cd "$(dirname "$REPORT_JSON")"

        sha256sum --check \
            "$(basename "$CHECKSUM_FILE")"
    ) || die "Report JSON checksum verification failed."
fi

PID_FILE="/tmp/genosphere_report_server_${USER}_${PORT}.pid"

LOG_FILE="/tmp/genosphere_report_server_${USER}_${PORT}.log"

if [[ -s "$PID_FILE" ]]; then
    OLD_PID="$(
        cat "$PID_FILE" 2>/dev/null || true
    )"

    if [[ "$OLD_PID" =~ ^[0-9]+$ ]] \
        && kill -0 "$OLD_PID" 2>/dev/null
    then
        kill "$OLD_PID" 2>/dev/null || true
        sleep 1
    fi

    rm -f "$PID_FILE"
fi

PORT_BUSY="$(
    python3 - "$PORT" <<'PY'
import socket
import sys

port = int(sys.argv[1])

with socket.socket() as sock:
    result = sock.connect_ex(("127.0.0.1", port))

print("yes" if result == 0 else "no")
PY
)"

[[ "$PORT_BUSY" == "no" ]] || {
    echo "ERROR: Port $PORT is already in use."
    echo "Use another port, for example:"
    echo
    echo "bash clinical_report/open_case_report.sh \\"
    echo "    \"$CASE_ID\" \\"
    echo "    --port 8766"
    exit 1
}

nohup \
    python3 -m http.server \
        "$PORT" \
        --bind 127.0.0.1 \
        --directory "$PROJECT_ROOT" \
    >"$LOG_FILE" \
    2>&1 &

SERVER_PID=$!

printf '%s\n' "$SERVER_PID" > "$PID_FILE"

SERVER_READY="no"

for _attempt in {1..20}; do
    if python3 - "$PORT" <<'PY'
import sys
import urllib.request

port = int(sys.argv[1])

try:
    with urllib.request.urlopen(
        f"http://127.0.0.1:{port}/clinical_report/index.html",
        timeout=1,
    ) as response:
        raise SystemExit(
            0 if response.status == 200 else 1
        )
except Exception:
    raise SystemExit(1)
PY
    then
        SERVER_READY="yes"
        break
    fi

    sleep 0.25
done

if [[ "$SERVER_READY" != "yes" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
    rm -f "$PID_FILE"

    echo "ERROR: Local report server did not start."
    echo "Log:"
    echo "$LOG_FILE"
    exit 1
fi

DATA_PATH="/results/cases/$CASE_ID/final/report/${CASE_ID}.report_draft.json"

REPORT_URL="http://127.0.0.1:${PORT}/clinical_report/index.html?data=${DATA_PATH}"

echo
echo "============================================================"
echo "CLINICAL REPORT BUILDER"
echo "============================================================"
echo "Case ID:       $CASE_ID"
echo "Report JSON:   $REPORT_JSON"
echo "Local server:  http://127.0.0.1:${PORT}"
echo "Report URL:    $REPORT_URL"
echo "Server PID:    $SERVER_PID"
echo "Server log:    $LOG_FILE"
echo

powershell.exe -NoProfile -Command     "Start-Process '$REPORT_URL'"

echo "The report was opened in the Windows browser."
echo
echo "To stop the server later, run:"
echo
echo "kill $SERVER_PID"

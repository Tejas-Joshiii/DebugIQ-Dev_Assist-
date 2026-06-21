#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
  "$PROJECT_DIR/.venv/bin/python" "$SCRIPT_DIR/devassist.py" "$@"
elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
  "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/devassist.py" "$@"
else
  python3 "$SCRIPT_DIR/devassist.py" "$@"
fi

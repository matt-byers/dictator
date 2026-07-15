#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h:h}"
PYTHON="${PYTHON:-python3.13}"
[[ -d "$ROOT/.venv" ]] || "$PYTHON" -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/.venv/bin/python" -m pip install -e '.[macos,dev]'

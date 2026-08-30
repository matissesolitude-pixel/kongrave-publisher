#!/usr/bin/env zsh
# XAUUSD range/sweep -- chaine complete.
# macOS : caffeinate -di empeche la mise en veille pendant le telechargement long.
set -euo pipefail
cd "$(dirname "$0")"

[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip install -q -r requirements.txt

export PYTHONPATH="$PWD/src"
PY=./.venv/bin/python

case "${1:-all}" in
  test)
    $PY tests/test_classify.py
    $PY tests/selftest.py
    ;;
  download)  caffeinate -di $PY -m grs.cli download "${@:2}" ;;
  aggregate) $PY -m grs.cli aggregate "${@:2}" ;;
  sessions)  $PY -m grs.cli sessions "${@:2}" ;;
  report)    $PY -m grs.cli report "${@:2}" ;;
  all)       caffeinate -di $PY -m grs.cli all "${@:2}" ;;
  *)         echo "usage: ./run.sh {test|download|aggregate|sessions|report|all}"; exit 1 ;;
esac

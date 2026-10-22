#!/bin/bash
# Daily refresh (run after 4:15 PM ET on trading days). Order matters.
# Data files live in ./data (override with EP304_DATA_DIR).
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
$PY pull.py            # -> data/prices.json  (latest close, 52-wk high, 200-day avg)
$PY ta.py              # -> data/ta.json      (5y daily + weekly bars, completed sessions only)
$PY ta_verdict.py      # -> verdicts in data/ta.json (+ data/ta_block.ts)
$PY portfolio.py point # -> today's value point appended to data/ledger.json (trades untouched)

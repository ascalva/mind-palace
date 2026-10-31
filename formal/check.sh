#!/bin/sh
# The local L1 gate (dn-mathematical-foundations §2.4): build the statements and run their attacks,
# hold the sorry count to the budget, and keep the axiom escape shut.
set -eu
cd "$(dirname "$0")"

lake build

budget=$(cat sorry-budget)
count=$(cat Palace.lean Palace/*.lean | grep -ow sorry | wc -l | tr -d ' ')
if [ "$count" -gt "$budget" ]; then
  echo "sorry count $count exceeds the budget $budget" >&2
  exit 1
fi
if [ "$count" -lt "$budget" ]; then
  echo "sorry count $count is below the budget $budget: lower sorry-budget to $count" >&2
  exit 1
fi

if grep -nwE 'axiom|admit|native_decide' Palace.lean Palace/*.lean; then
  echo "axiom escape: the lines above" >&2
  exit 1
fi
lake env lean Audit.lean

echo "L1 gate green: sorry $count of budget $budget, standard axioms only"

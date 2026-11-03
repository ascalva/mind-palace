#!/bin/sh
# The L1 gate (dn-mathematical-foundations §2.4), run locally and by the advisory `lean` CI job:
# build the library, run its attacks, lint it, hold the sorry count to the budget, keep the axiom
# escape shut, and check the cross-reference between docs/LAWS.md and the statements.
set -eu
cd "$(dirname "$0")"

lake build # Palace: the definitions and proofs, nothing run at build time
lake test  # PalaceTest: every Plausible attack and negative control
lake lint  # Batteries' environment linters over Palace
lake exe mk_all --check --lib Palace
lake exe mk_all --check --lib PalaceTest

budget=$(cat sorry-budget)
count=$(cat Palace.lean Palace/*.lean PalaceTest.lean PalaceTest/*.lean | grep -ow sorry | wc -l | tr -d ' ')
if [ "$count" -gt "$budget" ]; then
  echo "sorry count $count exceeds the budget $budget" >&2
  exit 1
fi
if [ "$count" -lt "$budget" ]; then
  echo "sorry count $count is below the budget $budget: lower sorry-budget to $count" >&2
  exit 1
fi

if grep -nwE 'axiom|admit|native_decide' Palace.lean Palace/*.lean PalaceTest.lean PalaceTest/*.lean
then
  echo "axiom escape: the lines above" >&2
  exit 1
fi
lake env lean Audit.lean
python3 ../scripts/check_laws_xref.py

echo "L1 gate green: sorry $count of budget $budget, standard axioms only, ledger cross-referenced"

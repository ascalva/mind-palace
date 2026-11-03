#!/bin/sh
# The L1 gate (dn-mathematical-foundations §2.4), run locally and by the advisory `lean` CI job:
# build the library and its specification, run the attacks, lint, hold the sorry count to the
# budget, keep the axiom escape shut, judge the library against the specification, and check the
# cross-reference between docs/LAWS.md and the statements.
set -eu
cd "$(dirname "$0")"

lake build --wfail Palace # the model and the proofs: nothing runs at build time, nothing warns
lake build --log-level=error Spec # the statements, each proof `sorry` by design
lake test # PalaceTest: every Plausible attack and negative control
lake lint # Batteries' environment linters over Palace
for lib in Palace PalaceTest Spec; do
  lake exe mk_all --check --lib "$lib"
done

budget=$(cat sorry-budget)
count=$(cat Palace.lean Palace/*.lean Palace/*/*.lean PalaceTest.lean PalaceTest/*.lean |
  grep -ow sorry | wc -l | tr -d ' ')
if [ "$count" -gt "$budget" ]; then
  echo "sorry count $count exceeds the budget $budget" >&2
  exit 1
fi
if [ "$count" -lt "$budget" ]; then
  echo "sorry count $count is below the budget $budget: lower sorry-budget to $count" >&2
  exit 1
fi

if grep -nwE 'axiom|admit|native_decide' Palace.lean Palace/*.lean Palace/*/*.lean \
  PalaceTest.lean PalaceTest/*.lean Spec.lean Spec/*.lean; then
  echo "axiom escape: the lines above" >&2
  exit 1
fi
lake env lean Audit.lean

# The judge (comparator.json): the library proves exactly the statements in Spec/, from the
# standard axioms, and everything those statements reach passes Lean's kernel and, with
# --paranoid, five independent checkers. It builds and exports both sides in a bwrap sandbox,
# which is Linux's; elsewhere the same comparison runs in-process and CI runs the judge.
if command -v bwrap > /dev/null 2>&1; then
  lake comparator --paranoid
else
  echo "no bwrap here: comparing in-process; CI runs lake comparator --paranoid" >&2
  lake env lean --run Compare.lean
fi
python3 ../scripts/check_laws_xref.py

echo "L1 gate green: sorry $count of budget $budget, standard axioms only, the specification" \
  "judged, ledger cross-referenced"

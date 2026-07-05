#!/usr/bin/env bash
# BP-002 acceptance harness — verifies amendment A3 (journal-gate (c) made
# untracked-inclusive over the blessing surfaces) and finding-0004's ambient-path
# exclusion, while keeping BP-000 (criteria 1–7) and BP-001 (A1/A2) green. Run from
# the repo root:
#   bash docs/build-plans/bp-002/acceptance/run.sh
#
# A3  = the Stop-gate (c) blessing detector reads *untracked* plan/design paths, so a
#       plan minted fresh through Bash directly at `status: ready` — invisible both to
#       `git diff HEAD` (tracked-only) and to gate-guard (Edit/Write matcher only) — is
#       caught as a from-nothing blessing. Symmetric to A1's own (b) fix; the last of
#       the three owner-only blessings to be closed against the Bash write path (§6c).
# 0004 = `.claude/settings.local.json` is gitignored, so the permission cache's churn
#        never reaches the audit's working-tree diff (the ambient-path exclusion).
#
# The new checks run in ISOLATED throwaway git repos (CLAUDE_PROJECT_DIR pointed at a
# temp dir holding a copy of the hooks) so real committed / uncommitted / untracked
# blessing states are staged without touching the main repo. The prior harnesses are
# invoked by reference — bp-001's run.sh already wraps bp-000's and snapshot-restores
# bp-000/journal.md — so all 18 prior criteria stay green with no extra bookkeeping.
set -u
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
export CLAUDE_PROJECT_DIR="$ROOT"
H=".claude/hooks"
PTR=".claude/state/active-plan"
SAVED_PTR="$(cat "$PTR" 2>/dev/null || true)"
pass=0; fail=0
ok(){ echo "  PASS — $1"; pass=$((pass+1)); }
no(){ echo "  FAIL — $1"; fail=$((fail+1)); }
restore(){ printf '%s\n' "$SAVED_PTR" > "$PTR"; }
trap restore EXIT

# Stand up an isolated temp git repo with a copy of the hooks + an initial commit
# (so HEAD exists and the only later delta is what a test stages). Sets the varname
# passed as $1 to the temp dir path.
mk_temp_repo(){
  local td; td="$(mktemp -d -t bp002-XXXX)"
  mkdir -p "$td/.claude/hooks" "$td/.claude/state"
  cp "$H/_lib.py" "$td/.claude/hooks/_lib.py"
  cp "$H/journal-gate.sh" "$td/.claude/hooks/journal-gate.sh"
  git -C "$td" init -q
  git -C "$td" config user.email bp002@test.local
  git -C "$td" config user.name  bp002-harness
  git -C "$td" add -A
  git -C "$td" commit -qm 'init: hooks' >/dev/null
  printf -v "$1" '%s' "$td"
}
# Run the real journal-gate Stop audit against a temp repo ($1); stderr merged.
jg(){ CLAUDE_PROJECT_DIR="$1" bash "$1/.claude/hooks/journal-gate.sh" --standalone 2>&1; }

echo "════════════════════════════════════════════════════════════════════"
echo "PRIOR — BP-000 (1–7) + BP-001 (A1/A2) must stay green (18/18, by reference)"
echo "────────────────────────────────────────────────────────────────────"
# bp-001's harness wraps bp-000's and restores bp-000/journal.md itself, so both
# prior deltas re-run without leaving the main worktree dirty. Its full output is
# captured; only the two SUMMARY lines are surfaced here.
PRIORLOG="$(mktemp -t bp002-prior-XXXX.log)"
bash docs/build-plans/bp-001/acceptance/run.sh >"$PRIORLOG" 2>&1; prior_rc=$?
grep -E "^SUMMARY" "$PRIORLOG" | sed 's/^/     /'
if [ "$prior_rc" = 0 ]; then
  ok "BP-000 (1–7) + BP-001 (A1/A2) all green (prior harness exit 0)"
else
  no "a prior criterion regressed (prior harness exit $prior_rc)"
  echo "     (prior harness tail:)"; tail -25 "$PRIORLOG" | sed 's/^/     /'
fi
rm -f "$PRIORLOG"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "0005-regression — a Bash-minted plan at status: ready BLOCKS close (A3, §6c)"
echo "────────────────────────────────────────────────────────────────────"
# Orchestrator posture (no active-plan pointer) so (a) and (b) cannot fire — the (c)
# untracked-inclusive scan is the SOLE guard. The plan is written straight to disk
# (Bash), never Edit/Write and never `git add`, so it is invisible to gate-guard and
# to `git diff HEAD`. This is the exact finding-0005 escape.
mk_temp_repo T
mkdir -p "$T/docs/build-plans/xx"
printf -- '---\ntype: build-plan\nid: xx\nstatus: ready\n---\n' > "$T/docs/build-plans/xx/plan.md"
out="$(jg "$T")"; rc=$?
echo "     rc=$rc ; reason: $out"
{ [ "$rc" = 2 ] && printf '%s' "$out" | grep -qi "blessing" \
    && printf '%s' "$out" | grep -q "xx/plan.md"; } \
  && ok "untracked ready plan caught by (c) (rc=2, reason cites blessing + the file)" \
  || no "untracked ready plan NOT blocked — A3 regressed (the finding-0005 hole is open)"
rm -rf "$T"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "0005-legit — a Bash-minted plan at status: proposed does NOT block (A3, §14)"
echo "────────────────────────────────────────────────────────────────────"
# A newly minted plan is legitimate only at status: proposed — this is exactly what
# /graduate emits. The A3 scan must be tight enough not to block it, or it would
# break legitimate plan creation (the §14 parked-denylist's scoping caveat).
mk_temp_repo T
mkdir -p "$T/docs/build-plans/yy"
printf -- '---\ntype: build-plan\nid: yy\nstatus: proposed\n---\n' > "$T/docs/build-plans/yy/plan.md"
out="$(jg "$T")"; rc=$?
echo "     rc=$rc ; reason: ${out:-<none — ALLOW>}"
{ [ "$rc" = 0 ]; } \
  && ok "untracked proposed plan does NOT block — /graduate creation is unimpeded" \
  || no "proposed plan wrongly blocked — A3 is over-broad (would break /graduate)"
rm -rf "$T"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "committed-blessing — a committed → ready plan self-clears, rc=0 (A1 preserved)"
echo "────────────────────────────────────────────────────────────────────"
# Bless the plan, then COMMIT it: it is now accountable to its commit author (§10,
# 'deliberate, logged'). A1's HEAD-anchored (c) must self-clear a committed blessing,
# and the A3 untracked scan must not re-flag it — a committed file is tracked, hence
# never in `git ls-files --others`. This is the guarantee A3 must leave intact.
mk_temp_repo T
mkdir -p "$T/docs/build-plans/zz"
printf -- '---\ntype: build-plan\nid: zz\nstatus: proposed\n---\n' > "$T/docs/build-plans/zz/plan.md"
git -C "$T" add -A; git -C "$T" commit -qm 'propose zz' >/dev/null
printf -- '---\ntype: build-plan\nid: zz\nstatus: ready\n---\n' > "$T/docs/build-plans/zz/plan.md"
git -C "$T" add -A; git -C "$T" commit -qm 'ready zz' >/dev/null   # committed blessing
out="$(jg "$T")"; rc=$?
echo "     rc=$rc ; reason: ${out:-<none — ALLOW>}"
{ [ "$rc" = 0 ] && ! printf '%s' "$out" | grep -qi "blessing"; } \
  && ok "committed → ready plan self-clears vs HEAD (rc=0) — A1 behavior preserved by A3" \
  || no "committed ready plan still blocked — A3 broke the A1 self-clear"
rm -rf "$T"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "(c)-uncommitted-plan — an in-place proposed→ready flip still blocks (A1, §6c)"
echo "────────────────────────────────────────────────────────────────────"
# Complements the committed case and bp-001's design-note flip: an *uncommitted*
# in-place proposed→ready flip on a tracked plan is caught by the tracked (c) path
# (`_blessing_in_diff`), unchanged by A3.
mk_temp_repo T
mkdir -p "$T/docs/build-plans/ww"
printf -- '---\ntype: build-plan\nid: ww\nstatus: proposed\n---\n' > "$T/docs/build-plans/ww/plan.md"
git -C "$T" add -A; git -C "$T" commit -qm 'propose ww' >/dev/null
printf -- '---\ntype: build-plan\nid: ww\nstatus: ready\n---\n' > "$T/docs/build-plans/ww/plan.md"  # uncommitted, tracked
out="$(jg "$T")"; rc=$?
echo "     rc=$rc ; reason: $out"
{ [ "$rc" = 2 ] && printf '%s' "$out" | grep -qi "blessing"; } \
  && ok "uncommitted in-place proposed→ready flip still blocks (tracked (c) path holds)" \
  || no "uncommitted plan flip not blocked — the tracked (c) path regressed"
rm -rf "$T"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "0004 — settings.local.json churn no longer trips the gate (ambient-path excl.)"
echo "────────────────────────────────────────────────────────────────────"
# before/after around the finding-0004 fix. A builder plan is active (scope = its
# src/**); the permission system mutates .claude/settings.local.json mid-build.
mk_temp_repo T
mkdir -p "$T/docs/build-plans/tw/src"
cat > "$T/docs/build-plans/tw/plan.md" <<'EOF'
---
type: build-plan
id: tw
status: in-progress
write_scope:
  - "docs/build-plans/tw/src/**"
---
EOF
printf '# journal\n' > "$T/docs/build-plans/tw/journal.md"
printf '%s\n' "docs/build-plans/tw/plan.md" > "$T/.claude/state/active-plan"
printf '{"permissions":{}}\n' > "$T/.claude/settings.local.json"
# [before] finding-0004's reported state: the file is TRACKED (force-added past the
# machine-global ignore) and out-of-scope, so a mid-build permission-cache write
# trips the (b) scope audit through no fault of the builder.
git -C "$T" add -A; git -C "$T" add -f .claude/settings.local.json
git -C "$T" commit -qm 'plan + journal + (tracked) settings.local.json' >/dev/null
touch "$T/docs/build-plans/tw/journal.md"                                  # (a) passes
printf '{"permissions":{"allow":["Bash(one)"]}}\n' > "$T/.claude/settings.local.json"
out_b="$(jg "$T")"; rc_b=$?
echo "     [before — tracked]    rc=$rc_b ; names-settings=$(printf '%s' "$out_b" | grep -c 'settings.local.json')"
# [after] the finding-0004 fix (a): remove from the index + gitignore, COMMITTED once
# (the note's 'requires committing its removal from the index once'). The file is now
# ambient — never in `git status --porcelain -uall`, so its churn is invisible.
printf '.claude/settings.local.json\n' >> "$T/.gitignore"
git -C "$T" rm --cached -q .claude/settings.local.json
git -C "$T" add .gitignore; git -C "$T" commit -qm 'untrack + gitignore settings.local.json (finding-0004)' >/dev/null
touch "$T/docs/build-plans/tw/journal.md"
printf '{"permissions":{"allow":["Bash(one)","Bash(two)"]}}\n' > "$T/.claude/settings.local.json"
out_a="$(jg "$T")"; rc_a=$?
echo "     [after — gitignored]  rc=$rc_a ; reason: ${out_a:-<none — ALLOW>}"
{ [ "$rc_b" = 2 ] && printf '%s' "$out_b" | grep -q 'settings.local.json' && [ "$rc_a" = 0 ]; } \
  && ok "settings.local.json trips (b) only while tracked; gitignored, its churn no longer trips (0004)" \
  || no "finding-0004 ambient-path exclusion not effective"
rm -rf "$T"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "SUMMARY (bp-002): PASS=$pass  FAIL=$fail"
echo "════════════════════════════════════════════════════════════════════"
[ "$fail" = 0 ]

#!/usr/bin/env bash
# BP-001 acceptance harness — verifies amendments A1 and A2 and keeps the BP-000
# criteria 1–7 green. Run from the repo root:
#   bash docs/build-plans/bp-001/acceptance/run.sh
#
# A1 = journal-gate (c) diffs the working tree against HEAD (a committed blessing
#      self-clears; only an uncommitted flip blocks) + (b) is untracked-inclusive.
# A2 = the domain non-negotiables digest is re-homed inline into CLAUDE.md.
#
# The new (c)/(b) checks run in ISOLATED throwaway git repos: CLAUDE_PROJECT_DIR
# is pointed at a temp dir holding a copy of the hooks, so real committed and
# uncommitted blessing states can be staged without touching the main repo. Each
# temp repo writes a STALE session-baseline to prove enforcement no longer reads
# it — under the old (diff-vs-baseline) code the (c)-committed check would fail.
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

# Stand up an isolated temp git repo with a copy of the hooks. Sets the varname
# passed as $1 to the temp dir path.
mk_temp_repo(){
  local td; td="$(mktemp -d -t bp001-XXXX)"
  mkdir -p "$td/.claude/hooks" "$td/.claude/state"
  cp "$H/_lib.py" "$td/.claude/hooks/_lib.py"
  cp "$H/journal-gate.sh" "$td/.claude/hooks/journal-gate.sh"
  git -C "$td" init -q
  git -C "$td" config user.email bp001@test.local
  git -C "$td" config user.name  bp001-harness
  printf -v "$1" '%s' "$td"
}
# Run the real journal-gate Stop audit against a temp repo ($1); stderr merged.
jg(){ CLAUDE_PROJECT_DIR="$1" bash "$1/.claude/hooks/journal-gate.sh" --standalone 2>&1; }

echo "════════════════════════════════════════════════════════════════════"
echo "PRIOR — BP-000 criteria 1–7 must stay green (re-run by reference)"
echo "────────────────────────────────────────────────────────────────────"
# The BP-000 harness appends a HOOK-FAILURE marker to the (sealed) bp-000 journal
# in criterion 7. Snapshot-restore it so bp-000/** is left byte-identical and out
# of this bp-001 session's write delta (bp-000/** is not in bp-001 write_scope).
JSNAP="$(mktemp -t bp000-journal-XXXX)"
cp docs/build-plans/bp-000/journal.md "$JSNAP"
bash docs/build-plans/bp-000/acceptance/run.sh; prior_rc=$?
cp "$JSNAP" docs/build-plans/bp-000/journal.md; rm -f "$JSNAP"
echo "────────────────────────────────────────────────────────────────────"
[ "$prior_rc" = 0 ] && ok "BP-000 criteria 1–7 all green (bp-000 harness exit 0)" \
                    || no "a BP-000 criterion regressed (bp-000 harness exit $prior_rc)"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "(c)-uncommitted — an uncommitted '→ ratified' flip blocks close (A1, §6c)"
echo "────────────────────────────────────────────────────────────────────"
mk_temp_repo T
mkdir -p "$T/docs/design-notes"
printf -- '---\ntype: design-note\nid: dn-throwaway\nstatus: draft\n---\n' \
  > "$T/docs/design-notes/throwaway.md"
git -C "$T" add -A; git -C "$T" commit -qm 'draft note' >/dev/null
git -C "$T" rev-parse HEAD > "$T/.claude/state/session-baseline"   # STALE (pre-flip)
# Uncommitted blessing: draft -> ratified, left in the working tree.
printf -- '---\ntype: design-note\nid: dn-throwaway\nstatus: ratified\n---\n' \
  > "$T/docs/design-notes/throwaway.md"
out="$(jg "$T")"; rc=$?
echo "     rc=$rc ; reason: $out"
{ [ "$rc" = 2 ] && printf '%s' "$out" | grep -qi "blessing"; } \
  && ok "uncommitted → ratified flip blocks close (rc=2, reason cites blessing)" \
  || no "uncommitted blessing not blocked"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "(c)-committed — a committed '→ ratified' flip self-clears, rc=0 (A1, §6c)"
echo "────────────────────────────────────────────────────────────────────"
# Commit the flip; HEAD now carries the ratification. The STALE baseline still
# points at the pre-flip commit — under the old diff-vs-baseline code this kept
# firing (the finding-0003 addendum loop). Against HEAD it self-clears.
git -C "$T" add -A; git -C "$T" commit -qm 'ratify note' >/dev/null
out="$(jg "$T")"; rc=$?
echo "     rc=$rc ; reason: ${out:-<none — ALLOW>}"
{ [ "$rc" = 0 ] && ! printf '%s' "$out" | grep -qi "blessing"; } \
  && ok "committed → ratified flip self-clears vs HEAD (rc=0, no blessing block)" \
  || no "committed blessing still blocked (baseline re-anchor loop not fixed)"
rm -rf "$T"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "(b)-regression — an untracked out-of-scope file still blocks close (A1, §6b)"
echo "────────────────────────────────────────────────────────────────────"
mk_temp_repo T
mkdir -p "$T/docs/build-plans/tw" "$T/core"
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
git -C "$T" add -A; git -C "$T" commit -qm 'plan + journal' >/dev/null
touch "$T/docs/build-plans/tw/journal.md"   # mtime > last commit so (a) passes
: > "$T/core/rogue.txt"                       # untracked, out-of-scope, Bash-style write
out="$(jg "$T")"; rc=$?
echo "     rc=$rc ; reason: $out"
{ [ "$rc" = 2 ] && printf '%s' "$out" | grep -q "core/rogue.txt"; } \
  && ok "untracked out-of-scope file caught by (b) (rc=2, names the file)" \
  || no "untracked out-of-scope file not blocked (criterion 2 regressed)"
rm -rf "$T"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "digest — the domain non-negotiables are re-homed inline in CLAUDE.md (A2, §5)"
echo "────────────────────────────────────────────────────────────────────"
present=1
while IFS= read -r marker; do
  [ -z "$marker" ] && continue
  if grep -qiF "$marker" CLAUDE.md; then echo "     present: $marker"
  else echo "     MISSING: $marker"; present=0; fi
done <<'MARKERS'
non-negotiable
Sealed core has zero network egress
model advises; code acts
Self-modification is gated
fixed points are sacred
Voice/telephony is bounded
MARKERS
[ "$present" = 1 ] && ok "non-negotiables digest present inline in CLAUDE.md (§5, A2)" \
                   || no "digest not re-homed"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "SUMMARY (bp-001): PASS=$pass  FAIL=$fail"
echo "════════════════════════════════════════════════════════════════════"
[ "$fail" = 0 ]

#!/usr/bin/env bash
# BP-004 acceptance harness — verifies amendment A5 (finding-0006, status-value
# normalization) and A6 (finding-0008, template + command reconciliation), while
# keeping BP-000 (1–7) + BP-001 (A1/A2) + BP-002 (A3/0004) green. Run from the repo
# root:
#   bash docs/build-plans/bp-004/acceptance/run.sh
#
# A5 = the parser normalizes a status value (strips a trailing ' #' YAML comment,
#      space-hash only) before the THREE blessing detectors compare it by exact
#      equality, so a comment-bearing `status: ready   # x` is recognized as a
#      blessing on all three paths — pre-hoc gate-guard (hook/stdin), Stop-gate
#      tracked (`_blessing_in_diff`), Stop-gate untracked (`_untracked_blessing`).
#      The no-space case `ready#x` is deliberately NOT stripped (never fabricate a
#      blessing), and a '#' in a non-status field is untouched (scope is status-only).
# A6 = the template's status line carries no inline comment (A5 hygiene) and
#      `re_entry` is restored as a front-matter key; the command files read
#      context_manifest/acceptance/non_goals/stop_conditions from the §2/§7/§9/§10
#      body sections, not front-matter keys.
#
# The A5 detector checks run in ISOLATED throwaway git repos (CLAUDE_PROJECT_DIR
# pointed at a temp dir holding a copy of the hooks) so real tracked / untracked
# blessing states are staged without touching the main repo. gate-guard is driven
# in HOOK mode (stdin JSON) — its real PreToolUse path — because `--standalone`
# passes the status raw, bypassing the extractor where normalization lives. The
# prior harnesses are invoked by reference (bp-002 wraps bp-001 wraps bp-000, and
# each snapshot-restores what it dirties) so all 18 prior criteria stay green.
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

# Stand up an isolated temp git repo with a copy of the three hooks the A5 checks
# drive (_lib.py + gate-guard.sh + journal-gate.sh) + an initial commit (so HEAD
# exists and the only later delta is what a test stages). Sets the varname passed
# as $1 to the temp dir path.
mk_temp_repo(){
  local td; td="$(mktemp -d -t bp004-XXXX)"
  mkdir -p "$td/.claude/hooks" "$td/.claude/state"
  cp "$H/_lib.py" "$td/.claude/hooks/_lib.py"
  cp "$H/gate-guard.sh" "$td/.claude/hooks/gate-guard.sh"
  cp "$H/journal-gate.sh" "$td/.claude/hooks/journal-gate.sh"
  git -C "$td" init -q
  git -C "$td" config user.email bp004@test.local
  git -C "$td" config user.name  bp004-harness
  git -C "$td" add -A
  git -C "$td" commit -qm 'init: hooks' >/dev/null
  printf -v "$1" '%s' "$td"
}
# Run the real journal-gate Stop audit against a temp repo ($1); stderr merged.
jg(){ CLAUDE_PROJECT_DIR="$1" bash "$1/.claude/hooks/journal-gate.sh" --standalone 2>&1; }
# Drive the real gate-guard in HOOK mode against a temp repo ($1) with stdin JSON
# ($2). The real PreToolUse path: cmd_gate_check_hook → _status_in_text (where A5's
# normalization lives) → cmd_gate_check. stderr merged; rc is gate-guard's.
gg(){ printf '%s' "$2" | CLAUDE_PROJECT_DIR="$1" bash "$1/.claude/hooks/gate-guard.sh" 2>&1; }
# Build a PreToolUse Edit/Write JSON for a plan.md whose new content sets $2 as the
# status line. `\n` are literal in the single-quoted printf arg → JSON newlines.
gjson(){ printf '%s' '{"tool_input":{"file_path":"docs/build-plans/gg/plan.md","content":"---\ntype: build-plan\nid: gg\n'"$1"'\n---\n"}}'; }

echo "════════════════════════════════════════════════════════════════════"
echo "PRIOR — BP-000 (1–7) + BP-001 (A1/A2) + BP-002 (A3/0004) stay green (18/18)"
echo "────────────────────────────────────────────────────────────────────"
# bp-002's harness wraps bp-001's (which wraps bp-000's) and each restores what it
# dirties, so the whole prior chain re-runs without leaving the main worktree dirty.
# It copies the CURRENT (A5-fixed) _lib.py into its temp repos — all prior tests use
# clean status lines, so the normalization is a no-op and they must stay green (the
# plan §3 Q7 guarantee: the A5 change never alters a clean-status verdict).
PRIORLOG="$(mktemp -t bp004-prior-XXXX.log)"
bash docs/build-plans/bp-002/acceptance/run.sh >"$PRIORLOG" 2>&1; prior_rc=$?
grep -E "^SUMMARY" "$PRIORLOG" | sed 's/^/     /'
if [ "$prior_rc" = 0 ]; then
  ok "BP-000+BP-001+BP-002 all green under the A5-fixed _lib.py (prior harness exit 0)"
else
  no "a prior criterion regressed under the A5 fix (prior harness exit $prior_rc)"
  echo "     (prior harness tail:)"; tail -25 "$PRIORLOG" | sed 's/^/     /'
fi
rm -f "$PRIORLOG"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "0006-strip / gate-guard (pre-hoc, HOOK mode) — comment-bearing ready DENIES"
echo "────────────────────────────────────────────────────────────────────"
# The real PreToolUse path. new_status flows through _status_in_text (normalized);
# cur = status_of(new file) = None ≠ ready → DENY. Control: clean `ready` also DENIES
# (proves the path is wired, non-vacuous). nospace `ready#x` must ALLOW (never
# fabricate a blessing).
mk_temp_repo T
out="$(gg "$T" "$(gjson 'status: ready   # x')")"; rc=$?
echo "     [comment] rc=$rc ; $out"
{ [ "$rc" = 2 ] && printf '%s' "$out" | grep -qi 'blessing\|ready'; } \
  && ok "gate-guard DENIES a comment-bearing 'ready   # x' (rc=2) — A5 fix fires pre-hoc" \
  || no "gate-guard did NOT deny the comment-bearing ready — A5 pre-hoc path open"
out="$(gg "$T" "$(gjson 'status: ready')")"; rc=$?
echo "     [control] rc=$rc ; $out"
{ [ "$rc" = 2 ]; } \
  && ok "control: clean 'ready' DENIES (rc=2) — the gate-guard path is wired (non-vacuous)" \
  || no "control clean 'ready' did NOT deny — gate-guard path not exercised"
out="$(gg "$T" "$(gjson 'status: ready#x')")"; rc=$?
echo "     [nospace] rc=$rc ; ${out:-<ALLOW>}"
{ [ "$rc" = 0 ]; } \
  && ok "nospace 'ready#x' ALLOWS (rc=0) — normalization never fabricates a blessing" \
  || no "nospace 'ready#x' wrongly denied — normalization over-fired (fabricated a blessing)"
rm -rf "$T"

echo
echo "════════════════════════════════════════════════════════════════════"
echo "0006-strip / Stop-gate TRACKED (_blessing_in_diff) — comment ready BLOCKS"
echo "────────────────────────────────────────────────────────────────────"
# Orchestrator posture (no active-plan pointer): (a)/(b) cannot fire, so the tracked
# (c) diff-vs-HEAD scan is the sole guard. Commit the plan at proposed, then flip it
# in place (uncommitted, TRACKED) — git diff HEAD shows `+status: ready   # x`, which
# _blessing_in_diff normalizes to `ready`.
tracked_case(){  # $1=status-line, expect rc in $2 (2=block,0=allow), $3=label
  mk_temp_repo T
  mkdir -p "$T/docs/build-plans/tk"
  printf -- '---\ntype: build-plan\nid: tk\nstatus: proposed\n---\n' > "$T/docs/build-plans/tk/plan.md"
  git -C "$T" add -A; git -C "$T" commit -qm 'propose tk' >/dev/null
  printf -- '---\ntype: build-plan\nid: tk\n%s\n---\n' "$1" > "$T/docs/build-plans/tk/plan.md"
  local out rc; out="$(jg "$T")"; rc=$?
  echo "     [$3] rc=$rc ; ${out:-<ALLOW>}"
  if [ "$2" = 2 ]; then
    { [ "$rc" = 2 ] && printf '%s' "$out" | grep -qi 'blessing'; } \
      && ok "tracked (c): '$1' BLOCKS (rc=2, cites blessing) — $3" \
      || no "tracked (c): '$1' did NOT block — $3"
  else
    { [ "$rc" = 0 ]; } \
      && ok "tracked (c): '$1' ALLOWS (rc=0) — $3" \
      || no "tracked (c): '$1' wrongly blocked — $3"
  fi
  rm -rf "$T"
}
tracked_case 'status: ready   # x' 2 'comment-bearing ready → block (A5)'
tracked_case 'status: ready'       2 'clean ready control → block (non-vacuous)'
tracked_case 'status: ready#x'     0 'nospace ready#x → allow (no fabrication)'

echo
echo "════════════════════════════════════════════════════════════════════"
echo "0006-strip / Stop-gate UNTRACKED (_untracked_blessing) — comment ready BLOCKS"
echo "────────────────────────────────────────────────────────────────────"
# A Bash-minted plan directly at a comment-bearing blessed status: untracked, so it
# is invisible to git diff HEAD and to gate-guard — caught only by the untracked scan
# reading status_of() (normalized). Orchestrator posture; the file is never `git add`ed.
untracked_case(){  # $1=status-line, expect rc in $2, $3=label
  mk_temp_repo T
  mkdir -p "$T/docs/build-plans/uk"
  printf -- '---\ntype: build-plan\nid: uk\n%s\n---\n' "$1" > "$T/docs/build-plans/uk/plan.md"
  local out rc; out="$(jg "$T")"; rc=$?
  echo "     [$3] rc=$rc ; ${out:-<ALLOW>}"
  if [ "$2" = 2 ]; then
    { [ "$rc" = 2 ] && printf '%s' "$out" | grep -qi 'blessing' \
        && printf '%s' "$out" | grep -q 'uk/plan.md'; } \
      && ok "untracked (c): '$1' BLOCKS (rc=2, cites blessing + file) — $3" \
      || no "untracked (c): '$1' did NOT block (or missed the file) — $3"
  else
    { [ "$rc" = 0 ]; } \
      && ok "untracked (c): '$1' ALLOWS (rc=0) — $3" \
      || no "untracked (c): '$1' wrongly blocked — $3"
  fi
  rm -rf "$T"
}
untracked_case 'status: ready   # x' 2 'comment-bearing ready → block (A5)'
untracked_case 'status: ready'       2 'clean ready control → block (non-vacuous)'
untracked_case 'status: ready#x'     0 'nospace ready#x → allow (no fabrication)'

echo
echo "════════════════════════════════════════════════════════════════════"
echo "0006-scope — a '#' in a NON-status field is untouched; status strips only"
echo "────────────────────────────────────────────────────────────────────"
# Direct-on-the-fixed-_lib.py unit assertions: the general `_scalar`/`parse_front_matter`
# path keeps a '#', while the status-specific extractors strip a ' #' comment.
scope_out="$(python3 - "$ROOT" <<'PY' 2>&1
import sys
sys.path.insert(0, sys.argv[1] + "/.claude/hooks")
import _lib
assert _lib._scalar("bar # keep") == "bar # keep", "scalar mangled"
assert _lib._normalize_status("ready # x") == "ready", "status not stripped"
assert _lib._normalize_status("ready#x") == "ready#x", "nospace stripped (would fabricate)"
fm = _lib.parse_front_matter(
    "---\ntype: build-plan\ndesign_ref: docs/x.md # keep\nstatus: ready # strip\n---\n")
assert fm["design_ref"] == "docs/x.md # keep", "non-status field mangled: %r" % fm["design_ref"]
assert _lib._status_in_text("status: ready # strip") == "ready", "status_in_text not stripped"
print("SCOPE-OK")
PY
)"
if printf '%s' "$scope_out" | grep -q "SCOPE-OK"; then
  ok "'#' survives in non-status fields; only the status path strips a ' #' comment"
else
  no "scope leak — the fix touched a non-status field: $scope_out"
fi

echo
echo "════════════════════════════════════════════════════════════════════"
echo "A5/A6 TEMPLATE — status line clean; re_entry a front-matter key; 4 fields body"
echo "────────────────────────────────────────────────────────────────────"
TPL="docs/templates/build-plan.md"
# status line 4 carries no inline comment.
if [ "$(sed -n '4p' "$TPL")" = "status: proposed" ]; then
  ok "template status line is 'status: proposed' with no inline comment (A5)"
else
  no "template status line still carries a comment: $(sed -n '4p' "$TPL")"
fi
# re_entry restored as a front-matter key (scan the first front-matter block only).
if awk '/^---$/{c++} c==1 && /^re_entry:/{found=1} c==2{exit} END{exit !found}' "$TPL"; then
  ok "template restores 're_entry' as a front-matter key (A6, greppable parked-gate)"
else
  no "template front-matter is missing the 're_entry' key (A6)"
fi
# the four moved fields must NOT be front-matter keys (they are body sections).
if awk '/^---$/{c++} c==1 && /^(objective|context_manifest|non_goals|stop_conditions):/{bad=1} c==2{exit} END{exit bad}' "$TPL"; then
  ok "objective/context_manifest/non_goals/stop_conditions stay body sections, not front-matter (A6)"
else
  no "a body-section field leaked back into the template front-matter (A6)"
fi
# and their body sections are still present.
if grep -qE '^## 1\. Objective' "$TPL" && grep -qE '^## 2\. Context manifest' "$TPL" \
   && grep -qE '^## 9\. Non-goals' "$TPL" && grep -qE '^## 10\. Stop-and-raise' "$TPL"; then
  ok "§1/§2/§9/§10 body sections present in the template"
else
  no "a required body section (§1/§2/§9/§10) is missing from the template"
fi

echo
echo "════════════════════════════════════════════════════════════════════"
echo "A6 COMMANDS — build/graduate/scribe read the moved fields from body sections"
echo "────────────────────────────────────────────────────────────────────"
# The four moved fields must be referenced as §2/§7/§9/§10 body sections, and no
# command may still instruct reading context_manifest as a front-matter key.
if grep -q '§2 Context manifest' .claude/commands/build.md \
   && grep -q '§7' .claude/commands/build.md \
   && grep -q '§9 Non-goals' .claude/commands/build.md \
   && grep -q '§10 Stop-and-raise' .claude/commands/build.md; then
  ok "build.md reads §2 manifest / §7 acceptance / §9 non-goals / §10 stop-conditions (A6)"
else
  no "build.md does not reference the §2/§7/§9/§10 body sections (A6)"
fi
if grep -q '§2 context' .claude/commands/graduate.md && grep -q '§7' .claude/commands/graduate.md; then
  ok "graduate.md emits §2 context manifest + §7 per-item acceptance (A6)"
else
  no "graduate.md does not reference the §2/§7 body sections (A6)"
fi
if grep -q '§2 context manifest' .claude/commands/scribe.md; then
  ok "scribe.md sets the §2 context manifest as a body section (A6)"
else
  no "scribe.md does not reference the §2 context manifest body section (A6)"
fi
if grep -q 'context_manifest' .claude/commands/build.md .claude/commands/graduate.md .claude/commands/scribe.md; then
  no "a command still names 'context_manifest' as a front-matter key (A6 drift remains)"
else
  ok "no command still names 'context_manifest' as a front-matter key (A6 drift closed)"
fi

echo
echo "════════════════════════════════════════════════════════════════════"
echo "FINDINGS promoted (Item 5; RED until the promotion lands, then green)"
echo "────────────────────────────────────────────────────────────────────"
# Item 5 is gated on this harness being green for Items 1–4 first, then promotes.
# These two assertions therefore turn green only after Item 5 lands — the terminal
# accounting trails the proven fix (plan §7 Item 5 falsifier: no premature promotion).
f6_st="$(awk -F': ' '/^status:/{print $2; exit}' docs/findings/finding-0006.md)"
if [ "$f6_st" = "promoted" ] && grep -qi 'A5' docs/findings/finding-0006.md && grep -qi 'bp-004' docs/findings/finding-0006.md; then
  ok "finding-0006 is promoted, resolution cites A5 + bp-004 (Item 5)"
else
  no "finding-0006 not yet promoted with an A5/bp-004 resolution (status=$f6_st) [expected RED pre-Item-5]"
fi
f8_st="$(awk -F': ' '/^status:/{print $2; exit}' docs/findings/finding-0008.md)"
if [ "$f8_st" = "promoted" ] && grep -qi 'A6' docs/findings/finding-0008.md && grep -qi 'bp-004' docs/findings/finding-0008.md; then
  ok "finding-0008 is promoted, resolution cites A6 + bp-004 (Item 5)"
else
  no "finding-0008 not yet promoted with an A6/bp-004 resolution (status=$f8_st) [expected RED pre-Item-5]"
fi

echo
echo "════════════════════════════════════════════════════════════════════"
echo "SUMMARY (bp-004): PASS=$pass  FAIL=$fail"
echo "════════════════════════════════════════════════════════════════════"
[ "$fail" = 0 ]

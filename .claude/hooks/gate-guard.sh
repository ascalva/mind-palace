#!/usr/bin/env bash
# gate-guard — PreToolUse(Edit|Write|MultiEdit): deny blessing transitions.
# The two blessing gates — design-note draft→ratified and plan proposed→ready —
# are owner-manual, made by hand outside any agent session (design-note §10).
# This hook denies either transition pre-hoc, in every session and every role.
# All other status transitions (ready→in-progress→complete|parked|superseded)
# pass. Only fires on files under docs/design-notes/ and docs/build-plans/**/plan.md.
#
# Dual-mode:  hook (stdin JSON)  |  --standalone <file_path> <intended_status>
# Fail posture: fail-open, fail-loud (§6).
NAME="gate-guard"
# Worktree-aware ROOT (bp-014, warrant finding-0031): prefer the CWD worktree's own
# git toplevel over the inherited CLAUDE_PROJECT_DIR when they DIFFER and that toplevel
# carries its own .claude/state/ — so a hook firing inside a worktree reads THAT
# worktree's active-plan pointer, never the main checkout's (which the delegate harness
# sets CLAUDE_PROJECT_DIR to). Fail-closed: the worktree's own state governs its own
# writes; a broad main-checkout pointer never loosens a narrow worktree builder. Both
# sides realpath-normalized (pwd -P) so /tmp->/private/tmp symlink drift can't spoof the
# comparison. When they agree (or no .claude/state/), byte-identical to before. Kept in
# lock-step with _lib.py:repo_root().
_wt_norm() { [ -n "$1" ] && [ -d "$1" ] && (cd "$1" 2>/dev/null && pwd -P) || printf '%s' "$1"; }
_CWD_TOP="$(git rev-parse --show-toplevel 2>/dev/null)"; _CWD_TOP="$(_wt_norm "$_CWD_TOP")"
_ENV_TOP="$(_wt_norm "${CLAUDE_PROJECT_DIR:-}")"
if [ -n "$_CWD_TOP" ] && [ "$_CWD_TOP" != "$_ENV_TOP" ] && [ -d "$_CWD_TOP/.claude/state" ]; then
  ROOT="$_CWD_TOP"
else
  ROOT="${_ENV_TOP:-${_CWD_TOP:-$(pwd -P)}}"
fi
LIB="$ROOT/.claude/hooks/_lib.py"
HOOK_INTENTIONAL=0

fail_loud() {
  printf 'HOOK-FAILURE %s: %s — enforcement NOT applied\n' "$NAME" "$1" >&2
  python3 "$LIB" marker "HOOK-FAILURE $NAME: $1 — enforcement NOT applied" >/dev/null 2>&1 || true
}
trap 'rc=$?; [ "$HOOK_INTENTIONAL" = 1 ] || fail_loud "unexpected exit rc=$rc"' EXIT

if [ "${1:-}" = "--standalone" ]; then
  shift
  out="$(python3 "$LIB" gate-check "${1:-}" "${2:-}")"; rc=$?
else
  out="$(python3 "$LIB" gate-check-hook)"; rc=$?
fi

if [ "$rc" != 0 ]; then fail_loud "lib error (rc=$rc)"; HOOK_INTENTIONAL=1; exit 0; fi
case "$out" in
  ALLOW*) HOOK_INTENTIONAL=1; exit 0 ;;
  DENY:*) HOOK_INTENTIONAL=1; printf '%s\n' "${out#DENY: }" >&2; exit 2 ;;
  *)      fail_loud "unrecognized decision: $out"; HOOK_INTENTIONAL=1; exit 0 ;;
esac

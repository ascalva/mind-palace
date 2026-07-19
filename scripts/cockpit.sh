#!/usr/bin/env bash
# cockpit.sh — the owner's reading room (bp-072, decision-routing v1).
#
# Opens (or re-joins) an idempotent tmux session `palace`: a "desk" window with the
# docket open in vim on the left and a claude session on the right, and an "ops" window
# with system status + the daemon log. It reads; it never gates — the owner decides in
# dialogue and acts by keystroke (`palace bless`, ratify by hand, answer an oq).
#
# Idempotent: if the `palace` session already exists it is JOINED, never rebuilt — so a
# second invocation never mints a second session. Joining is $TMUX-aware: from OUTSIDE
# tmux it attaches; from INSIDE another session it switches the client (attach would nest).
#
# The cockpit owns the SESSION and its data (the generated docket, runtime focus-events);
# your dotfiles own the EDITOR. It touches no file outside the repo and needs no daemon.
#
# Usage:
#   ./scripts/cockpit.sh            # open or join the palace cockpit
#   ./scripts/cockpit.sh --dry-run  # print every tmux command it WOULD run; execute none

set -euo pipefail

SESSION=palace
# Repo root, derived from this script's own location (scripts/ -> repo root) — so panes
# root at the repo regardless of the caller's cwd.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="data/logs/palace.out.log"   # launchd StandardOut sink; exists whether or not the daemon is up (Q8)

DRY=0
[[ "${1:-}" == "--dry-run" ]] && DRY=1

# Echo-or-execute: in --dry-run every tmux call is printed with a leading '+' and NOT run.
run() {
  if [[ $DRY -eq 1 ]]; then
    printf '+ %s\n' "$*"
  else
    "$@"
  fi
}

build() {
  # desk: docket (regenerated) open in vim, left; a claude session, right.
  run tmux new-session -d -s "$SESSION" -c "$ROOT" -n desk
  run tmux send-keys -t "$SESSION:desk" "uv run scripts/docket.py --write && nvim .claude/state/docket.md" Enter
  run tmux split-window -h -t "$SESSION:desk" -c "$ROOT"
  # Pin the reading-room session to the router default (opus-medium) so it always opens at
  # the confirmed tier regardless of what a prior /model re-tier left saved globally; the
  # owner still re-tiers in place with /model for a design/gate turn.
  run tmux send-keys -t "$SESSION:desk.1" "claude --model opus[1m]" Enter
  run tmux select-pane -t "$SESSION:desk.0"          # leave focus on the reading pane
  # ops: system snapshot + a live daemon-log tail (never requires the daemon to be up).
  run tmux new-window -t "$SESSION" -n ops -c "$ROOT"
  run tmux send-keys -t "$SESSION:ops" "uv run scripts/palace.py status; tail -n 40 -F $LOG" Enter
  # status bar: the ambient awaiting-count, recomputed each minute.
  run tmux set -t "$SESSION" status-interval 60
  run tmux set -t "$SESSION" status-right "#(cd $ROOT && uv run scripts/docket.py --count) awaiting "
  # runtime focus-events — a server option, set ephemerally; no dotfile touched (Q6).
  run tmux set -s focus-events on
  run tmux select-window -t "$SESSION:desk"
}

join() {
  if [[ -n "${TMUX:-}" ]]; then
    run tmux switch-client -t "$SESSION"   # INSIDE tmux — switch, never nest
  else
    run tmux attach -t "$SESSION"          # OUTSIDE tmux — attach
  fi
}

main() {
  if [[ $DRY -eq 1 ]]; then
    echo "# cockpit (dry-run): session '$SESSION' — desk (vim-on-docket | claude) + ops (status + log)"
    echo "# idempotent: if session '$SESSION' exists -> join (NO rebuild); else build then join"
    echo "# join is \$TMUX-aware:  outside tmux -> tmux attach -t $SESSION   |   inside -> tmux switch-client -t $SESSION"
    build
    join
    return 0
  fi
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    join     # already built — jump in, never rebuild (idempotence)
  else
    build
    join
  fi
}

main "$@"

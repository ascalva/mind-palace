#!/usr/bin/env zsh
# ─────────────────────────────────────────────────────────────────────────────
# Mind Palace — project shell tooling
#
# Loaded via the `mp` bootstrap function in ~/.zshrc, which sources this file.
# Sourced into the current shell (NOT run as an executable) because several
# commands change shell state (mp-cd) or own your tmux session (mp-new).
#
# Layout convention, one per unit of work you name yourself:
#   label "integrity-verifier"  →  branch  claude-integrity-verifier
#                                →  worktree $MP_WT_DIR/mp-integrity-verifier
#                                →  tmux     mp-integrity-verifier
# ─────────────────────────────────────────────────────────────────────────────

# --- Configuration (self-locating; override any of these before `mp` if needed)
# %x = path of this sourced file; :A absolutize (resolve symlinks); :h:h up two
# (bin/ → repo root). Robust regardless of where the repo is cloned or how it's
# sourced.
MP_ROOT="${${(%):-%x}:A:h:h}"
export MP_ROOT
export MP_WT_DIR="${MP_WT_DIR:-$HOME}"   # where worktrees are created (repo siblings)
export MP_BASE="${MP_BASE:-main}"        # branch new work is cut from

# --- Sanity: is MP_ROOT actually the repo?
if ! git -C "$MP_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  echo "mp: '$MP_ROOT' is not a git repo — fix MP_ROOT or the mp() shim in ~/.zshrc" >&2
  return 1 2>/dev/null || exit 1
fi

# --- Internal helpers -------------------------------------------------------
_mp_label_ok() {  # labels become branch/dir/session names: keep them safe
  [[ "$1" == [A-Za-z0-9][A-Za-z0-9_-]# ]] && return 0
  echo "mp: label must be alphanumeric with - or _ (no spaces/slashes): '$1'" >&2
  return 1
}
_mp_on_base() { [[ "$(git -C "$MP_ROOT" symbolic-ref --short HEAD 2>/dev/null)" == "$MP_BASE" ]]; }
_mp_clean()   { [[ -z "$(git -C "$MP_ROOT" status --porcelain)" ]]; }

# --- Start (or reattach to) a build session --------------------------------
# usage: mp-new <label>          e.g. mp-new integrity-verifier
mp-new() {
  local label="$1"
  [[ -z "$label" ]] && { echo "usage: mp-new <label>"; return 1; }
  _mp_label_ok "$label" || return 1

  local branch="claude-$label" path="$MP_WT_DIR/mp-$label" session="mp-$label"

  if [[ -d "$path" ]]; then
    echo "mp: worktree exists ($path) — reattaching"
  else
    git -C "$MP_ROOT" rev-parse --verify --quiet "$MP_BASE" >/dev/null \
      || { echo "mp: base branch '$MP_BASE' not found"; return 1; }
    echo "mp: creating worktree $path on new branch $branch (from $MP_BASE)"
    git -C "$MP_ROOT" worktree add -b "$branch" "$path" "$MP_BASE" || return 1
  fi

  if tmux has-session -t "$session" 2>/dev/null; then
    tmux attach -t "$session"
  else
    # caffeinate -is holds the machine awake exactly as long as claude runs;
    # exec zsh leaves an interactive shell in the worktree when claude exits.
    tmux new -s "$session" -c "$path" "caffeinate -is claude; exec zsh"
  fi
}

# --- Orchestrator session in the main root ---------------------------------
mp-orch() {
  local s="mp-orchestrator"
  if tmux has-session -t "$s" 2>/dev/null; then
    tmux attach -t "$s"
  else
    tmux new -s "$s" -c "$MP_ROOT" "caffeinate -is claude; exec zsh"
  fi
}

# --- Attach to / jump into an existing session or worktree -----------------
mp-attach() {  # usage: mp-attach <label>   (reattach without create logic)
  local s="mp-$1"
  tmux has-session -t "$s" 2>/dev/null && tmux attach -t "$s" \
    || echo "mp: no tmux session '$s' (see: mp-ls)"
}
mp-cd() {      # usage: mp-cd <label>   — cd this shell into the worktree
  local path="$MP_WT_DIR/mp-$1"
  [[ -d "$path" ]] && cd "$path" || echo "mp: no worktree at $path"
}

# --- See what's in flight ---------------------------------------------------
mp-ls() {
  echo "worktrees:"
  git -C "$MP_ROOT" worktree list
  echo "\ntmux sessions:"
  tmux ls 2>/dev/null | grep '^mp-' || echo "  (none)"
}

# --- Preview what a branch would merge (read-only) --------------------------
# usage: mp-review <label>
mp-review() {
  local branch="claude-$1"
  git -C "$MP_ROOT" rev-parse --verify --quiet "$branch" >/dev/null \
    || { echo "mp: branch $branch not found"; return 1; }
  echo "commits on $branch not yet in $MP_BASE:"
  git -C "$MP_ROOT" log --oneline "$MP_BASE..$branch"
  echo "\nfiles changed:"
  git -C "$MP_ROOT" diff --stat "$MP_BASE...$branch"
}

# --- Merge a finished plan/branch into main --------------------------------
# usage: mp-finish <label>   (reviews, confirms, --no-ff merges; does NOT push)
mp-finish() {
  local label="$1" branch="claude-$1"
  [[ -z "$label" ]] && { echo "usage: mp-finish <label>"; return 1; }
  git -C "$MP_ROOT" rev-parse --verify --quiet "$branch" >/dev/null \
    || { echo "mp: branch $branch not found"; return 1; }
  _mp_clean   || { echo "mp: main worktree has uncommitted changes — commit/stash first"; return 1; }
  _mp_on_base || { echo "mp: main worktree isn't on $MP_BASE — switch it there first"; return 1; }

  mp-review "$label"; echo
  local reply
  read "reply?merge $branch into $MP_BASE (--no-ff)? [y/N] "
  [[ "$reply" == [yY] ]] || { echo "aborted"; return 1; }

  if git -C "$MP_ROOT" merge --no-ff "$branch"; then
    echo "\nmerged. next:  mp-push   then  mp-cleanup $label"
  else
    echo "\nmerge conflicts — resolve in $MP_ROOT, then commit the merge"
    return 1
  fi
}

# --- Push main to the remote (explicit, separate step) ---------------------
mp-push() { git -C "$MP_ROOT" push "$@"; }

# --- Tear down a worktree + branch after merge -----------------------------
# usage: mp-cleanup <label>   (refuses to delete unmerged work without override)
mp-cleanup() {
  local label="$1" branch="claude-$1" path="$MP_WT_DIR/mp-$1" session="mp-$1"
  [[ -z "$label" ]] && { echo "usage: mp-cleanup <label>"; return 1; }

  if git -C "$MP_ROOT" branch --merged "$MP_BASE" | grep -qw "$branch"; then
    [[ -d "$path" ]] && git -C "$MP_ROOT" worktree remove "$path"
    git -C "$MP_ROOT" branch -d "$branch" 2>/dev/null
  else
    echo "mp: WARNING — $branch is not merged into $MP_BASE."
    local reply
    read "reply?remove worktree and DELETE unmerged branch anyway? [y/N] "
    [[ "$reply" == [yY] ]] || { echo "aborted — nothing removed"; return 1; }
    [[ -d "$path" ]] && git -C "$MP_ROOT" worktree remove --force "$path"
    git -C "$MP_ROOT" branch -D "$branch" 2>/dev/null
  fi

  git -C "$MP_ROOT" worktree prune
  tmux kill-session -t "$session" 2>/dev/null
  echo "cleaned up $label"
}

# --- Help -------------------------------------------------------------------
mp-help() {
  cat <<'EOF'
Mind Palace tooling:
  mp-new <label>      create worktree+branch+tmux and start claude (or reattach)
  mp-orch             orchestrator session in the main repo root
  mp-attach <label>   reattach to an existing session
  mp-cd <label>       cd this shell into a worktree
  mp-ls               list worktrees and mp- tmux sessions
  mp-review <label>   preview commits+diff a branch would merge (read-only)
  mp-finish <label>   review, confirm, --no-ff merge into main (no push)
  mp-push             push main to the remote
  mp-cleanup <label>  remove worktree + branch after merge

Lifecycle:  mp-new X → (work) → commit → mp-review X → mp-finish X → mp-push → mp-cleanup X
Detach a session with Ctrl-b d; reattach with mp-new X or mp-attach X.
Note: mp-new cuts from your LOCAL $MP_BASE — `git -C "$MP_ROOT" pull` first if multi-machine.
EOF
}

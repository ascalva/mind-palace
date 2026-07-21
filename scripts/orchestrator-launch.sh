#!/usr/bin/env bash
# orchestrator-launch.sh — the cockpit's orchestrator-pane launcher (dn-plane-principals §3.2).
#
# PLANE toggle (finding-0125) selects the principal this pane runs as:
#   ascalva  (DEFAULT) -> plain login launch as the invoking user, where the FABLE tier is available
#                          for design/gate work. Workflow-plane isolation is OFF for this pane.
#   workflow (opt-in)  -> the isolated ouroboros-work WORKFLOW principal (this file's original job).
#                          Fable is NOT reachable there: the headless `setup-token` credential it
#                          authenticates with does not expose fable (finding-0125).
# Default swapped to ascalva by the owner 2026-07-20: with fable broken on the role account, the
# human-login pane is the common case. Opt into isolation per-pane with `PLANE=workflow`.
#
# The workflow plane runs Claude Code as ouroboros-work with the two secrets it needs made available
# at launch, sourced from ascalva's login keychain (only ascalva can read them) and handed across the
# sudo boundary via the ENVIRONMENT only — NEVER the repo (#10) and NEVER a command line (argv is
# world-readable; a process's environment is visible to its owner and root only). The sudoers env_keep
# whitelist (plane-migration.md §6) is what lets these named vars cross.
#
#   - CLAUDE_CODE_OAUTH_TOKEN : subscription OAuth, headless (`claude setup-token`)     [finding-0120]
#   - PALACE_SIGN_PASS        : the ssh signing-key passphrase, read per-commit by       [finding-0122]
#                               sign-askpass.sh so `ssh-keygen -Y sign` signs silently
#
# Owner one-time setup (docs/runbooks/plane-migration.md §4/§5/§6):
#   security add-generic-password -U -s claude-oauth-token     -a ouroboros-work -w <setup-token>
#   security add-generic-password -U -s ssh-signing-passphrase -a ouroboros-work -w <key passphrase>
#   sudoers Defaults:ascalva env_keep += "CLAUDE_CODE_OAUTH_TOKEN PALACE_SIGN_PASS SSH_ASKPASS SSH_ASKPASS_REQUIRE"
#
# Fail-safe: if ouroboros-work is not provisioned yet (pre-migration), the workflow plane launches
# plainly as the invoking user so the cockpit still opens a working pane.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EFFORT="${2:-high}"; PERM="${3:-auto}"   # default effort medium→high (owner rule 2026-07-21)
PLANE="${PLANE:-ascalva}"

# --- workflow plane (opt-in): the isolated ouroboros-work principal ---------------------------
# Only PLANE=workflow takes the role-account path; the default and anything else launch as the human
# login below (fable available). Model pins opus[1m] here (fable is unreachable under this auth, and
# the pin overrides the global fable default).
if [ "$PLANE" = "workflow" ]; then
  MODEL="${1:-opus[1m]}"

  # Pre-migration / un-provisioned -> plain launch as whoever we are (no plane split yet).
  if ! id ouroboros-work >/dev/null 2>&1; then
    echo "orchestrator-launch: ouroboros-work not provisioned — launching as $(id -un) (pre-migration; docs/runbooks/plane-migration.md)." >&2
    exec claude --model "$MODEL" --effort "$EFFORT" --permission-mode "$PERM"
  fi

  # Read secrets from the INVOKING user's (ascalva's) keychain. The first access may raise a one-time
  # Keychain approval dialog — click "Always Allow" so future launches are silent.
  _kc() { security find-generic-password -s "$1" -a ouroboros-work -w 2>/dev/null; }

  CLAUDE_CODE_OAUTH_TOKEN="$(_kc claude-oauth-token || true)"
  if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
    echo "orchestrator-launch: keychain item 'claude-oauth-token' missing/empty — run 'claude setup-token' and store it (plane-migration.md §5)." >&2
    exit 1
  fi
  PALACE_SIGN_PASS="$(_kc ssh-signing-passphrase || true)"   # optional; if absent, signed commits prompt
  if [ -z "${PALACE_SIGN_PASS:-}" ]; then
    echo "orchestrator-launch: WARNING — no 'ssh-signing-passphrase' in keychain; signed commits will prompt for it (plane-migration.md §4)." >&2
  fi

  export CLAUDE_CODE_OAUTH_TOKEN PALACE_SIGN_PASS
  export SSH_ASKPASS="$ROOT/scripts/sign-askpass.sh" SSH_ASKPASS_REQUIRE=force

  # The four named vars cross the boundary via sudoers env_keep (§6). `-H` gives ouroboros-work its
  # OWN $HOME (its ~/.claude, separate Anthropic credential state); the OAuth token in the env is what
  # authenticates it.
  #
  # umask: sudo resets it to 0022 (verified) regardless of the invoking shell, and claude is exec'd
  # directly so ~/.zshrc's `umask 002` never runs — files would land 0644 (NOT group-writable), and
  # ascalva could then not hand-edit what the orchestrator creates (e.g. bless a plan it graduated).
  # Force 002 INSIDE the sudo'd process via a one-line sh, so new files honor the shared-repo (§3)
  # co-write (0664). env_keep vars are inherited by the sh and then by claude.
  exec sudo -u ouroboros-work -H /bin/sh -c \
    'umask 002; exec claude --model "$1" --effort "$2" --permission-mode "$3"' \
    orchestrator-launch "$MODEL" "$EFFORT" "$PERM"
fi

# --- ascalva plane (DEFAULT): plain login as the invoking user; fable available ---------------
# No sudo, no role split, no OAuth-token/askpass injection: the login user already has its own
# Anthropic credential AND global git signing config. Model is left to the owner (pass arg 1, or pick
# via /model in-session) so it inherits the global settings default (fable) and a wrong/renamed fable
# id can never break the launch and strand the cockpit pane.
echo "orchestrator-launch: plane=ascalva (default) — launching as $(id -un); fable-tier available for design/gate work (finding-0125). Set PLANE=workflow for the isolated ouroboros-work principal." >&2
MODEL="${1:-}"
if [ -n "$MODEL" ]; then
  exec claude --model "$MODEL" --effort "$EFFORT" --permission-mode "$PERM"
fi
exec claude --effort "$EFFORT" --permission-mode "$PERM"

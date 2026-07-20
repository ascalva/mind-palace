#!/usr/bin/env bash
# orchestrator-launch.sh — the cockpit's orchestrator-pane launcher (dn-plane-principals §3.2).
#
# Runs Claude Code as the ouroboros-work WORKFLOW principal with the two secrets it needs made
# available at launch, sourced from ascalva's login keychain (only ascalva can read them) and
# handed across the sudo boundary via the ENVIRONMENT only — NEVER the repo (#10) and NEVER a
# command line (argv is world-readable; a process's environment is visible to its owner and root
# only). The sudoers env_keep whitelist (plane-migration.md §6) is what lets these named vars cross.
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
# Toggle: `PLANE=ascalva` launches this pane as the invoking login user (fable-tier available for
# design/gate work) instead of the isolated ouroboros-work principal — see finding-0125.
#
# Fail-safe: if ouroboros-work is not provisioned yet (pre-migration), launch plainly as the
# invoking user so the cockpit still opens a working pane.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EFFORT="${2:-medium}"; PERM="${3:-auto}"

# PLANE selects the principal this pane runs as:
#   workflow (default) -> ouroboros-work, the isolated build/orchestration principal (this file's job)
#   ascalva            -> plain login as the invoking user, which RETAINS fable-tier access for
#                          design/gate passes (finding-0125: the headless `setup-token` credential the
#                          workflow plane authenticates with does NOT expose fable; the interactive
#                          login does). Flip per-pane with `PLANE=ascalva`; default stays isolated.
PLANE="${PLANE:-workflow}"

# --- ascalva plane: the fable/design escape hatch ---------------------------------------------
# Launch as the invoking user — no sudo, no role split, no OAuth-token/askpass injection: the login
# user already has its own Anthropic credential AND global git signing config. Model is left to the
# owner (pass arg 1, or pick via /model in-session) so a wrong/renamed fable id can never break the
# launch and strand the cockpit pane.
if [ "$PLANE" = "ascalva" ]; then
  echo "orchestrator-launch: PLANE=ascalva — launching as $(id -un); fable-tier available for design/gate work (finding-0125). Workflow-plane isolation is OFF for this pane." >&2
  MODEL="${1:-}"
  if [ -n "$MODEL" ]; then
    exec claude --model "$MODEL" --effort "$EFFORT" --permission-mode "$PERM"
  fi
  exec claude --effort "$EFFORT" --permission-mode "$PERM"
fi

# --- workflow plane (default): the ouroboros-work isolated principal --------------------------
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

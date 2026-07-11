#!/bin/sh
# Inject mind-palace secrets from macOS Keychain into the process environment, then exec the real
# command (runbook §0). `get_secret(name)` reads os.environ, and these names are hyphenated, so
# they're set via env(1) — shell `export` can't take hyphenated names. No secret is written to
# disk: each lives only in Keychain and this process's memory.
#
# Point the supervisor/watcher LaunchAgent's ProgramArguments at this wrapper:
#   [ .../scripts/run_with_secrets.sh, .../uv, run, .../scripts/watch.py ]
#
# A secret you haven't provisioned yet resolves to empty — which is falsy, so the layer that needs
# it stays fail-closed (e.g. [attestation] enabled = true with no key is a hard error). Place only
# the ones whose layer you've turned on.
set -eu

kc() { security find-generic-password -a mind-palace -s "$1" -w 2>/dev/null || true; }

exec env \
  "attestation-signing-key=$(kc attestation-signing-key)" \
  "attestation-owner-key=$(kc attestation-owner-key)" \
  "vault-supervisor-token=$(kc vault-supervisor-token)" \
  "$@"

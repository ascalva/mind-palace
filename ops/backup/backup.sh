#!/bin/sh
# Scheduled encrypted backup (BUILD-SPEC §16b, Phase 9). Invoked by com.mind-palace.backup.plist.
# restic encrypts + deduplicates CLIENT-SIDE, so only ciphertext reaches S3 — AWS never sees
# plaintext. Secrets are read from Keychain into the environment HERE (never written to disk or a
# command line); restic + vault inherit them.
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
# uv owns env resolution (CONVENTIONS §Language); absolute path — launchd PATH is minimal.
py() { /opt/homebrew/bin/uv run --directory "$REPO_ROOT" python "$@"; }

kc() { security find-generic-password -a mind-palace -s "$1" -w 2>/dev/null || true; }

# --- secrets + region into the env restic reads (S3 repo URL carries the rest) ---
RESTIC_PASSWORD="$(kc restic-password)"
AWS_ACCESS_KEY_ID="$(kc backup-aws-access-key-id)"
AWS_SECRET_ACCESS_KEY="$(kc backup-aws-secret-access-key)"
AWS_DEFAULT_REGION="$(py -c 'from config.loader import get_config; print(get_config().backup.region)')"
export RESTIC_PASSWORD AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION
[ -n "$RESTIC_PASSWORD" ] || { echo "FATAL: no restic-password in Keychain" >&2; exit 1; }

# --- best-effort consistent Vault snapshot (full DR) ---
# Staged inside the data dir so it rides along in the data backup below. If Vault is sealed /
# unreachable, or no backup token is placed, skip it and still back up everything else.
: "${VAULT_ADDR:=http://127.0.0.1:8200}"
export VAULT_ADDR
VAULT_TOKEN="$(kc vault-backup-token)"
export VAULT_TOKEN
mkdir -p data/backup-staging
if [ -n "$VAULT_TOKEN" ] && vault status >/dev/null 2>&1; then
  if vault operator raft snapshot save data/backup-staging/vault-raft.snap; then
    echo "vault snapshot saved"
  else
    echo "WARN: vault snapshot failed; continuing with data backup" >&2
  fi
else
  echo "WARN: vault-backup-token absent or Vault unreachable; skipping vault snapshot" >&2
fi

# --- ensure the repo exists (first run inits it; later runs skip) ---
py -m ops.backup.run snapshots >/dev/null 2>&1 || py -m ops.backup.run init

# --- backup -> retention prune -> integrity check (argv built + reviewed in ops/backup/plan.py) ---
py -m ops.backup.run backup
py -m ops.backup.run forget
py -m ops.backup.run check
echo "backup complete"

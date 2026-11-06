#!/bin/sh
# Apply the kv engine, the seven role policies, and one token role per agent policy to a running,
# UNSEALED Vault (runbook §2b). Owner-run: requires VAULT_ADDR and an authenticated VAULT_TOKEN
# (root, or a token with enough sudo) in the environment. Idempotent — safe to re-run.
# Places NO secrets — secret VALUES and the supervisor token are separate, manual steps below.
set -eu

# Ouroboros only (DI-2): this configures Ouroboros's Vault and its role policies. A named instance (MIND_PALACE_OVERLAY)
# is refused before anything is read or started.
if [ -n "${MIND_PALACE_OVERLAY:-}" ]; then
  echo "FATAL: $(basename "$0") is Ouroboros's; refusing under MIND_PALACE_OVERLAY" >&2
  exit 1
fi
: "${VAULT_ADDR:?export VAULT_ADDR=http://127.0.0.1:8200}"
: "${VAULT_TOKEN:?export VAULT_TOKEN, e.g. \$(security find-generic-password -a mind-palace -s vault-root-token -w)}"
cd "$(cd "$(dirname "$0")/../.." && pwd)"

# kv-v2 for static secrets — the mount path must equal [secrets] kv_mount = "kv".
if ! vault secrets list -format=json | grep -q '"kv/"'; then
  vault secrets enable -version=2 -path=kv kv
fi

# One narrow policy per role (ops/vault/policies/*.hcl is the audited grant table).
for f in ops/vault/policies/*.hcl; do
  vault policy write "$(basename "$f" .hcl)" "$f"
done

# One token role per AGENT policy: a scoped supervisor mints a token carrying that policy WITHOUT
# holding it, because the role's allowed_policies is the authorizer (see VaultClient.mint_token and
# supervisor.hcl). `supervisor` is excluded on purpose — it is the minter, not a mintable child.
for role in dreamer bridge research-airlock advisor correlator gate; do
  vault write "auth/token/roles/$role" \
    allowed_policies="$role" \
    token_explicit_max_ttl="1h" \
    orphan=false \
    renewable=true
done

echo "OK: kv engine + 7 policies + 6 token roles applied. (Verify: vault policy list)"
echo "Next (manual): place vault-supervisor-token in Keychain, load static secrets, set [secrets] enabled = true."

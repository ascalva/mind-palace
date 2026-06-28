# Vault AppRole policies

HCL policy documents for HashiCorp Vault as a per-interaction runtime authorization layer
(design-notes/vault-runtime-auth.md). Each file is the narrow grant for one agent role —
the dev-mode (`config/secrets_backend.py`) and real (`hvac`-backed) backends share the same
role names, so a policy written here is the production analogue of a `FakeVault(policies=...)`
fixture in tests.

| File | Role | Grant |
|------|------|-------|
| `dreamer.hcl` | `dreamer` | read `kv/oura-daily-aggregates` only |
| `bridge.hcl` | `bridge` | dynamic `aws/creds/bridge-role` + read `kv/oura-api-token` |
| `research-airlock.hcl` | `research-airlock` | dynamic `aws/creds/airlock-role` only |
| `advisor.hcl` | `advisor` | read `kv/financial-readonly-key` + `kv/oura-api-token` |
| `correlator.hcl` | `correlator` | read `kv/oura-daily-aggregates` only |
| `supervisor.hcl` | `supervisor` | `auth/token/create` only — mints, never reads role secrets |
| `gate.hcl` | `gate` | read/write `kv/gate-ledger-key` only |
| `backup.hcl` | `backup` | read `sys/storage/raft/snapshot` only — the scheduled backup's consistent Vault snapshot (Phase 9); sees no secret value |

Policies are narrow by default: grant the minimum, and the table above is the audit of *why*
each grant exists, so a future widening is a deliberate diff against this table, not a guess.

## Scaffolding (committed IaC — the build agent authored it; the owner runs it)

| File | What it is |
|------|-----------|
| `policies/*.hcl` | the seven role policies (table above) |
| `vault.hcl` | server config — Raft at `data/vault/raft`, loopback `127.0.0.1:8200` |
| `vault-unseal.sh` | starts the server + auto-unseals from Keychain (launchd-managed) |
| `com.mind-palace.vault.plist` | LaunchAgent template (RunAtLoad+KeepAlive), copy to `~/Library/LaunchAgents/` |
| `setup_policies.sh` | idempotent: enable kv, write the 7 policies, create 6 token roles |
| `setup_aws_engine.sh` | Phase B: configure the `aws` dynamic engine (after the airlock IAM exists) |

Minting goes through **token roles** (`auth/token/create/<role>`), so a *scoped* supervisor token
mints a token carrying a role's policy without holding that policy itself (see `supervisor.hcl` and
`VaultClient.mint_token`). `setup_policies.sh` was validated end-to-end against a real `vault
server -dev` — a non-root supervisor mints a working `dreamer` token yet is denied the secret.

## ⚠️ NOT applied to production — these are committed documents + scaffolding, not a live server

Nothing here has been run against a *production* Vault. Writing them is build-time work; applying
them (init/unseal, placing keys, loading real secrets) is owner-operated runtime work — same
build/owner split as the attestation keys (`ops/attestation/README.md`). **Full ordered steps are
in `docs/runbook.md` → "Security & trust infrastructure" §2.** The short version:

1. `vault server -config ops/vault/vault.hcl` (from the repo root) → `vault operator init`; place
   the unseal key + root token in Keychain (`vault-unseal-key`, `vault-root-token`); unseal.
2. `sh ops/vault/setup_policies.sh` (with `VAULT_ADDR`/`VAULT_TOKEN` set) — engines, policies, roles.
3. `vault token create -policy=supervisor -orphan -period=24h` → place at Keychain
   `vault-supervisor-token` (the bottom turtle for this layer, never stored in Vault).
4. Load the static secret values (`vault kv put kv/<name> value=…`) as you have them.
5. Install the LaunchAgent (auto-unseal on login); set `[secrets] enabled = true`.
6. (Phase B) After the airlock Terraform applies, `sh ops/vault/setup_aws_engine.sh`.

Until then, `[secrets] enabled = false` (the default) and `get_secret(name)` with no token keeps
reading env/Keychain exactly as it always has — this layer is additive, not a cutover.

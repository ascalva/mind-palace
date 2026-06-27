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

Policies are narrow by default: grant the minimum, and the table above is the audit of *why*
each grant exists, so a future widening is a deliberate diff against this table, not a guess.

## ⚠️ NOT applied — these are committed documents, not live policy

Nothing here has been run against a Vault server. Writing them is build-time work (code review,
git history); applying them is owner-operated runtime work, same build/owner split as the
attestation keys (`ops/attestation/README.md`).

**Production application is owner-operated** (full steps in the Step 6 runbook):
1. Stand up Vault per vault-runtime-auth.md §1 (rootless Podman, loopback `127.0.0.1:8200`,
   Raft storage, unseal key in Keychain).
2. `vault policy write <role> ops/vault/policies/<role>.hcl` for each file above.
3. Enable the `kv` v2 and `aws` secrets engines; configure `bridge-role`/`airlock-role` IAM.
4. Create an AppRole (or token role) per name binding it to its policy.
5. Place the supervisor's own bootstrap credential via `get_secret("vault-supervisor-token")`
   (Keychain/env — the bottom turtle for this layer, never stored in Vault itself).
6. Set `[secrets] enabled = true` in config.

Until then, `[secrets] enabled = false` (the default) and `get_secret(name)` with no token
keeps reading env/Keychain exactly as it always has — this layer is additive, not a cutover.

# backups — encrypted backup store (Zone C, Phase 9)

Provisions the destination for `restic` backups (BUILD-SPEC §16b):

- **S3 bucket** `mind-palace-backups-<account>` — private, **versioned**, TLS-only, SSE-KMS by
  default. restic has *already* client-side-encrypted + deduplicated everything before upload, so
  **AWS never sees plaintext**; the bucket's SSE-KMS is defense in depth on top.
- **KMS CMK** (`alias/mind-palace-backups`, rotation on) — the SSE-KMS key. Privacy does not depend
  on it (restic's repo password does); it's an extra at-rest layer + a revocation lever.
- **`mind-palace-backup` IAM user** — what restic authenticates as. Scoped to exactly this bucket +
  this key. **Deliberately independent of Vault's AWS engine**: restore is the disaster-recovery
  path and must work when Vault is sealed/down — a dependency on Vault (whose own state we back up)
  would be circular.

## Apply

```sh
aws sso login --profile alberto-sso
AWS_PROFILE=alberto-sso terraform init      # uses the bootstrap state bucket
AWS_PROFILE=alberto-sso terraform plan
AWS_PROFILE=alberto-sso terraform apply
```

Then (runbook §4): mint the backup user's access key by hand (kept out of tfstate), place it +
the restic repo password in Keychain, copy `restic_repository` → config `[backup] repository`,
`restic init`, and install the scheduled job.

```sh
aws iam create-access-key --user-name mind-palace-backup --profile alberto-sso
```

## Validate offline (no credentials)

```sh
terraform init -backend=false && terraform validate && terraform fmt -check -recursive
```

## Boundary

The bytes that leave the Mac are restic ciphertext, never plaintext private data — this is the
§16b backup boundary (the analog of the airlock's de-identification boundary). The sealed core
never runs backups; the scheduled OS-level job (launchd) does, reading data dirs and writing
ciphertext to S3.

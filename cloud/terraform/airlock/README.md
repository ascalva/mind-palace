# airlock — research airlock infrastructure (Zone C)

Provisions the one-way research flow (BUILD-SPEC §16):

- **S3 bucket** `mind-palace-airlock-<account>` with two prefixes — `requests/` (de-identified
  criteria out) and `results/` (public literature in). Public access blocked, SSE-S3, TLS-only,
  short lifecycle expiry (it's a transit, not a store).
- **Fetcher Lambda** (`../../fetcher`), triggered by S3 PUT into `requests/`. Broad public
  aggregation → `results/`. Not in a VPC (needs public egress to the literature APIs).
- **Least-privilege IAM** — fetcher: `GetObject requests/*` + `PutObject results/*` + logs.
  Bridge role: `PutObject requests/*` + `GetObject/List results/*`. Nothing wider.

## Apply

```sh
aws sso login --profile alberto-sso
# one-time: create the state backend
cd ../bootstrap && AWS_PROFILE=alberto-sso terraform init && AWS_PROFILE=alberto-sso terraform apply
cd ../airlock
AWS_PROFILE=alberto-sso terraform init
AWS_PROFILE=alberto-sso terraform plan
AWS_PROFILE=alberto-sso terraform apply
```

Then copy outputs into `config/defaults.toml [airlock]`: `airlock_bucket` → `s3_bucket`, and
configure an AWS profile `mind-palace-bridge` that assumes `bridge_role_arn`:

```ini
# ~/.aws/config
[profile mind-palace-bridge]
role_arn       = <bridge_role_arn>
source_profile = alberto-sso
region         = us-east-1
```

## Vault AWS dynamic engine (Phase B)

`vault_engine.tf` also creates `mind-palace-vault` — the IAM user Vault's AWS secrets engine
authenticates as (`config/root`), scoped to **only** `sts:AssumeRole` on bridge-role. The bridge
role's trust includes it, so dynamic creds work even if you narrow `bridge_trusted_principal_arns`
to your SSO role. Output `vault_engine_user_name`. The access key is **not** in tfstate by design —
mint it by hand after apply and hand it to Vault. Full sequence: `docs/runbook.md` §3a.

## Validate offline (no credentials)

```sh
terraform init -backend=false
terraform validate
terraform fmt -check -recursive
```

## Boundary

The sealed core never appears here — only the bridge (Zone B) holds AWS credentials and
touches S3. The corpus never crosses; only de-identified criteria leave (Invariant 2 & 11).

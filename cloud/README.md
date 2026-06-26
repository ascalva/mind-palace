# cloud/ — Zone C (AWS)

Terraform-managed airlock + backups. Sees only de-identified topic criteria and public literature; never plaintext private data (BUILD-SPEC §16). Airlock built in Phase 8; backups are Phase 9.

- `terraform/bootstrap/` — one-time: the dedicated `mind-palace-tfstate-*` state bucket (local state; S3-native locking, no DynamoDB).
- `terraform/airlock/` — the airlock S3 bucket (`requests/`+`results/`), the fetcher Lambda, and least-privilege IAM (fetcher: read requests/ + write results/ + logs; bridge: write requests/ + read results/).
- `fetcher/` — the Lambda: broad public-literature aggregation (OpenAlex, Europe PMC, arXiv — key-free), dependency-free (stdlib + runtime boto3).

The one-way flow (§16): core emits de-identified criteria → `data/airlock/requests/` → the Zone-B **bridge** (`edge/bridge/`) PUTs to S3 `requests/` → fetcher writes public literature to S3 `results/` → bridge GETs to `data/airlock/results/` → core ranks **inside the walls** (`core/research/rank.py`). The sealed core never touches S3; only the bridge does, and it has no vault handle (Invariant 2 & 11).

Owner decisions (phase8-aws-decisions): account `054942746160`, SSO profile `alberto-sso`, region `us-east-1`, fresh dedicated state, Lambda compute (Fargate is a later escalation seam).

# bootstrap — Terraform state backend (run once)

Creates the dedicated `mind-palace-tfstate-<account>` state bucket. Keeps **local** state (it
can't store its own creation), so the only thing committed here is `*.tf`; the local state
file is git-ignored.

```sh
aws sso login --profile alberto-sso
cd cloud/terraform/bootstrap
AWS_PROFILE=alberto-sso terraform init
AWS_PROFILE=alberto-sso terraform apply
```

Then initialize the airlock against it:

```sh
cd ../airlock
AWS_PROFILE=alberto-sso terraform init   # uses backend.tf -> the state bucket
AWS_PROFILE=alberto-sso terraform apply
```

State locking uses S3-native lockfiles (`use_lockfile = true`, Terraform ≥ 1.10) — no
DynamoDB table required.

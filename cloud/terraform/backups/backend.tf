# Remote state in the bootstrap bucket (cloud/terraform/bootstrap). S3-native locking
# (`use_lockfile`, Terraform >= 1.10) — no DynamoDB lock table. Requires the bootstrap applied
# first. Offline `validate`/`fmt` (no AWS creds): `terraform init -backend=false && terraform validate`.
terraform {
  backend "s3" {
    bucket       = "mind-palace-tfstate-054942746160"
    key          = "backups/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

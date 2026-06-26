# Remote state in the bootstrap bucket (cloud/terraform/bootstrap). S3-native locking
# (`use_lockfile`, Terraform >= 1.10) — no DynamoDB lock table.
#
# Requires the bootstrap to be applied first. To `validate`/`fmt` this config OFFLINE (no AWS
# credentials), skip backend init:  `terraform init -backend=false && terraform validate`.
terraform {
  backend "s3" {
    bucket       = "mind-palace-tfstate-054942746160"
    key          = "airlock/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

# Bootstrap — create the Terraform *state* backend for mind-palace (run once, first).
#
# Chicken-and-egg: the remote state bucket can't store its own creation. So this tiny config
# keeps LOCAL state (committed-ignored) and provisions only the dedicated state bucket. After
# `apply`, the airlock config (../airlock) uses it as an S3 backend with native locking
# (`use_lockfile = true`, Terraform >= 1.10) — so no DynamoDB lock table is needed.
#
# Owner decision (phase8-aws-decisions): fresh, dedicated mind-palace-* state; never touches
# existing infra. Account 054942746160, region us-east-1.

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.account_id] # fail closed if pointed at the wrong account

  default_tags {
    tags = {
      Project   = "mind-palace"
      Zone      = "C"
      ManagedBy = "terraform"
      Component = "tfstate-bootstrap"
    }
  }
}

resource "aws_s3_bucket" "tfstate" {
  bucket = var.state_bucket_name
}

# Versioning: state history + recoverability (a corrupted apply can be rolled back).
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

# SSE-KMS (aws/s3) on the state bucket — defense in depth; state can contain resource metadata.
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# State is never public.
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Reject any non-TLS access to the state bucket.
resource "aws_s3_bucket_policy" "tfstate_tls_only" {
  bucket = aws_s3_bucket.tfstate.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource = [
        aws_s3_bucket.tfstate.arn,
        "${aws_s3_bucket.tfstate.arn}/*",
      ]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}

# The restic repository bucket. Everything restic writes here is ALREADY client-side encrypted +
# deduplicated, so AWS never sees plaintext (§16b). SSE-KMS (aws_kms_key.backups) is defense in
# depth on top; versioning + lifecycle guard against accidental repo deletion or corruption.
resource "aws_s3_bucket" "backups" {
  bucket = var.backup_bucket_name
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket                  = aws_s3_bucket.backups.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# A backup store, not a transit: keep version history so a bad `restic prune` or an accidental
# delete is recoverable. Lifecycle expires only NONCURRENT versions (current data stays).
resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.backups.arn
    }
    bucket_key_enabled = true # one data key per bucket-key window — fewer KMS calls, lower cost
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration { noncurrent_days = var.noncurrent_version_retention_days }
  }

  rule {
    id     = "abort-incomplete-mpu"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload { days_after_initiation = 1 }
  }
}

resource "aws_s3_bucket_policy" "backups_tls_only" {
  bucket = aws_s3_bucket.backups.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource = [
        aws_s3_bucket.backups.arn,
        "${aws_s3_bucket.backups.arn}/*",
      ]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}

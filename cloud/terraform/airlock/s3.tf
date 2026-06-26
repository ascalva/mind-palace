# The airlock bucket. Two logical prefixes (no "folder" resource exists in S3 — the prefixes
# are object-key conventions, and IAM is scoped to them):
#   requests/  outbound: de-identified criteria the bridge PUTs; the fetcher reads.
#   results/   inbound:  public literature the fetcher writes; the bridge GETs.
# The data here is non-private by construction (de-identified criteria + public papers), so
# SSE-S3 (AES256) is sufficient; SSE-KMS is reserved for the Phase-9 backups bucket.

resource "aws_s3_bucket" "airlock" {
  bucket = var.airlock_bucket_name
}

resource "aws_s3_bucket_public_access_block" "airlock" {
  bucket                  = aws_s3_bucket.airlock.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "airlock" {
  bucket = aws_s3_bucket.airlock.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# The airlock is a transit, not a store: expire objects so nothing lingers.
resource "aws_s3_bucket_lifecycle_configuration" "airlock" {
  bucket = aws_s3_bucket.airlock.id

  rule {
    id     = "expire-requests"
    status = "Enabled"
    filter { prefix = "requests/" }
    expiration { days = var.object_retention_days }
  }

  rule {
    id     = "expire-results"
    status = "Enabled"
    filter { prefix = "results/" }
    expiration { days = var.object_retention_days }
  }

  rule {
    id     = "abort-incomplete-mpu"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload { days_after_initiation = 1 }
  }
}

# Reject any non-TLS access.
resource "aws_s3_bucket_policy" "airlock_tls_only" {
  bucket = aws_s3_bucket.airlock.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource = [
        aws_s3_bucket.airlock.arn,
        "${aws_s3_bucket.airlock.arn}/*",
      ]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}

# A criteria request landing in requests/ triggers the fetcher.
resource "aws_s3_bucket_notification" "airlock" {
  bucket = aws_s3_bucket.airlock.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.fetcher.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "requests/"
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke]
}

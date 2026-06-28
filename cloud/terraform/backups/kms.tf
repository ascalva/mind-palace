# Customer-managed KMS key for SSE-KMS on the backups bucket — defense in depth UNDER restic's
# own client-side encryption. The bytes restic uploads are already encrypted + deduplicated; S3
# then encrypts that ciphertext again at rest with this key. restic never sees the key; AWS
# applies it server-side. So privacy does NOT depend on this key (restic's repo password does) —
# this is purely an extra at-rest layer and an access-revocation lever (disable the key → no reads).
resource "aws_kms_key" "backups" {
  description             = "mind-palace backups bucket SSE-KMS (defense in depth under restic)"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  # Root retains admin so IAM can delegate use — the standard non-lockout key policy. The backup
  # user gets only Encrypt/Decrypt/GenerateDataKey via its IAM policy (iam.tf), nothing on the key
  # policy directly.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "EnableRootAndIamDelegation"
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::${var.account_id}:root" }
      Action    = "kms:*"
      Resource  = "*"
    }]
  })
}

resource "aws_kms_alias" "backups" {
  name          = "alias/mind-palace-backups"
  target_key_id = aws_kms_key.backups.key_id
}

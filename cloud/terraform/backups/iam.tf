# Least-privilege identity restic authenticates as for the backup/restore job. Deliberately a
# DEDICATED user, INDEPENDENT of Vault's AWS engine: backup AND restore must work even when Vault
# is sealed or down — restore is the disaster-recovery path, and a circular dependency on Vault
# (whose own state is part of what we back up) would defeat the purpose. Scoped to exactly this
# one bucket + this one key.
#
# The access key is NOT created here, to keep a long-lived secret out of tfstate. After apply,
# mint it by hand and place it in Keychain (runbook §4):
#   aws iam create-access-key --user-name mind-palace-backup --profile alberto-sso
resource "aws_iam_user" "backup" {
  name = "mind-palace-backup"
  tags = { purpose = "restic-backup-restore" }
}

data "aws_iam_policy_document" "backup" {
  statement {
    sid       = "ResticObjects"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.backups.arn}/*"]
  }
  statement {
    sid       = "ResticBucket"
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [aws_s3_bucket.backups.arn]
  }
  # SSE-KMS PUT needs GenerateDataKey; GET needs Decrypt. Scoped to the backups key alone.
  statement {
    sid       = "ResticSseKms"
    actions   = ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
    resources = [aws_kms_key.backups.arn]
  }
}

resource "aws_iam_user_policy" "backup" {
  name   = "restic-backup-access"
  user   = aws_iam_user.backup.name
  policy = data.aws_iam_policy_document.backup.json
}

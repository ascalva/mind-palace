output "backup_bucket" {
  description = "The restic repository bucket."
  value       = aws_s3_bucket.backups.id
}

output "backup_user_name" {
  description = "IAM user restic authenticates as. Mint its access key by hand (kept out of tfstate) and place it in Keychain (runbook §4). Independent of Vault for DR."
  value       = aws_iam_user.backup.name
}

output "kms_key_arn" {
  description = "SSE-KMS key for the backups bucket (defense in depth under restic's own encryption)."
  value       = aws_kms_key.backups.arn
}

output "restic_repository" {
  description = "RESTIC_REPOSITORY value for the backup job (s3 repo URL). Copy into config [backup] repository."
  value       = "s3:s3.${var.region}.amazonaws.com/${aws_s3_bucket.backups.id}"
}

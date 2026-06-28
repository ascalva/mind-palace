variable "account_id" {
  description = "AWS account id (guardrail: provider refuses any other account)."
  type        = string
  default     = "054942746160"
}

variable "region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "backup_bucket_name" {
  description = "S3 bucket holding the restic repository (already client-side encrypted). Account-suffixed."
  type        = string
  default     = "mind-palace-backups-054942746160"
}

variable "noncurrent_version_retention_days" {
  description = "Days to keep noncurrent object versions before expiry. restic prunes its own data; bucket versioning is a safety net against accidental repo corruption or deletion."
  type        = number
  default     = 30
}

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

variable "airlock_bucket_name" {
  description = "S3 bucket for the airlock (requests/ out, results/ in). Account-suffixed."
  type        = string
  default     = "mind-palace-airlock-054942746160"
}

variable "object_retention_days" {
  description = "Lifecycle expiry for requests/ and results/ objects. The airlock is a transit, not a store — short-lived by design."
  type        = number
  default     = 14
}

variable "lambda_runtime" {
  description = "Lambda runtime for the fetcher."
  type        = string
  default     = "python3.12"
}

variable "lambda_timeout" {
  description = "Fetcher wall-clock timeout (seconds). Broad aggregation across public APIs."
  type        = number
  default     = 60
}

variable "lambda_memory" {
  description = "Fetcher memory (MB)."
  type        = number
  default     = 256
}

variable "log_retention_days" {
  description = "CloudWatch log retention for the fetcher."
  type        = number
  default     = 30
}

variable "bridge_trusted_principal_arns" {
  description = <<-EOT
    IAM principals allowed to assume the least-privilege bridge role (the local Zone-B bridge,
    via its SSO session). RECOMMENDED: set this to your SSO permission-set role ARN, e.g.
    "arn:aws:iam::054942746160:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_<name>_<id>".
    Default [] falls back to the account root (any same-account principal that itself has
    sts:AssumeRole) — convenient for a single-user account, but narrow it for real least
    privilege.
  EOT
  type        = list(string)
  default     = []
}

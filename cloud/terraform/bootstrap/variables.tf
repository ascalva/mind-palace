variable "account_id" {
  description = "AWS account id (guardrail: provider refuses any other account)."
  type        = string
  default     = "054942746160"
}

variable "region" {
  description = "AWS region for the state bucket."
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Terraform state bucket. Account-suffixed for global uniqueness."
  type        = string
  default     = "mind-palace-tfstate-054942746160"
}

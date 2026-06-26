output "airlock_bucket" {
  description = "The airlock S3 bucket. Copy into config [airlock] s3_bucket for the bridge."
  value       = aws_s3_bucket.airlock.id
}

output "fetcher_function_name" {
  description = "The research fetcher Lambda."
  value       = aws_lambda_function.fetcher.function_name
}

output "bridge_role_arn" {
  description = "Least-privilege role the local bridge assumes. Configure an AWS profile (mind-palace-bridge) that source_profiles alberto-sso and assumes this role."
  value       = aws_iam_role.bridge.arn
}

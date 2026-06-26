output "state_bucket" {
  description = "The Terraform state bucket. Wire this into ../airlock/backend.tf."
  value       = aws_s3_bucket.tfstate.id
}

output "state_region" {
  description = "Region of the state bucket."
  value       = var.region
}

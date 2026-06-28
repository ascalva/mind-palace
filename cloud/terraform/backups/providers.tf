terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.account_id] # guardrail: never touch another account

  default_tags {
    tags = {
      Project   = "mind-palace"
      Zone      = "C"
      ManagedBy = "terraform"
      Component = "backups"
    }
  }
}

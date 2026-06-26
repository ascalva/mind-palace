# Least-privilege IAM (Invariant: tight IAM; §16 "scope the fetcher to web egress + the two
# prefixes, nothing else"). Two identities, each scoped to one direction of the airlock:
#
#   fetcher (Lambda, Zone C):  GetObject requests/*  +  PutObject results/*  +  its own logs.
#   bridge  (local, Zone B):   PutObject requests/*  +  GetObject/List results/*.
#
# Neither can read the other's writes back; neither has any bucket-admin or cross-prefix
# access. The fetcher's "web egress" is a network property (no VPC), not an IAM grant.

locals {
  bridge_principals = length(var.bridge_trusted_principal_arns) > 0 ? var.bridge_trusted_principal_arns : ["arn:aws:iam::${var.account_id}:root"]
}

# --- Fetcher (Lambda) execution role ----------------------------------------------------
data "aws_iam_policy_document" "fetcher_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "fetcher" {
  name               = "mind-palace-research-fetcher"
  assume_role_policy = data.aws_iam_policy_document.fetcher_assume.json
}

data "aws_iam_policy_document" "fetcher" {
  # Read de-identified criteria from requests/ ONLY.
  statement {
    sid       = "ReadRequests"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.airlock.arn}/requests/*"]
  }
  # Write public literature to results/ ONLY.
  statement {
    sid       = "WriteResults"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.airlock.arn}/results/*"]
  }
  # Its own log stream, nothing wider.
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.fetcher.arn}:*"]
  }
}

resource "aws_iam_role_policy" "fetcher" {
  name   = "fetcher-access"
  role   = aws_iam_role.fetcher.id
  policy = data.aws_iam_policy_document.fetcher.json
}

# --- Bridge (local Zone-B) assumable role -----------------------------------------------
data "aws_iam_policy_document" "bridge_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = local.bridge_principals
    }
  }
}

resource "aws_iam_role" "bridge" {
  name               = "mind-palace-bridge"
  assume_role_policy = data.aws_iam_policy_document.bridge_assume.json
}

data "aws_iam_policy_document" "bridge" {
  # Send de-identified criteria out (requests/ only).
  statement {
    sid       = "WriteRequests"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.airlock.arn}/requests/*"]
  }
  # Read public literature back (results/ only).
  statement {
    sid       = "ReadResults"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.airlock.arn}/results/*"]
  }
  # List only the results/ prefix (to discover finished jobs).
  statement {
    sid       = "ListResults"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.airlock.arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["results/*"]
    }
  }
}

resource "aws_iam_role_policy" "bridge" {
  name   = "bridge-access"
  role   = aws_iam_role.bridge.id
  policy = data.aws_iam_policy_document.bridge.json
}

# The fetcher Lambda. Zips cloud/fetcher/ (dependency-free: stdlib + the runtime's boto3).
#
# NOTE on web egress: the function is intentionally NOT attached to a VPC, so it has public
# internet egress (via AWS-managed networking) to reach the literature APIs. It has no route
# to anything private; its only AWS permissions are GetObject requests/* + PutObject results/*
# + logs (see iam.tf). That is the §16 "scope the fetcher to web egress + the two prefixes".

data "archive_file" "fetcher" {
  type        = "zip"
  source_dir  = "${path.module}/../../fetcher"
  output_path = "${path.module}/.build/fetcher.zip"
  excludes    = ["README.md", "requirements.txt", "__pycache__"]
}

resource "aws_cloudwatch_log_group" "fetcher" {
  name              = "/aws/lambda/${local.fetcher_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "fetcher" {
  function_name = local.fetcher_name
  role          = aws_iam_role.fetcher.arn
  runtime       = var.lambda_runtime
  handler       = "handler.lambda_handler"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory

  filename         = data.archive_file.fetcher.output_path
  source_code_hash = data.archive_file.fetcher.output_base64sha256

  # Deliberately no vpc_config: the fetcher needs public egress to the literature APIs and
  # has no business reaching anything private.

  depends_on = [aws_cloudwatch_log_group.fetcher]
}

resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id   = "AllowS3Invoke"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.fetcher.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = aws_s3_bucket.airlock.arn
  source_account = var.account_id
}

locals {
  fetcher_name = "mind-palace-research-fetcher"
}

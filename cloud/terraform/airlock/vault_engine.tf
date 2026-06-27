# Vault AWS secrets engine bootstrap principal (Phase B; vault-runtime-auth.md §4).
#
# The Vault AWS dynamic engine mints short-lived (TTL=1h) creds by ASSUMING the bridge role on a
# caller's behalf. To do that, Vault authenticates to AWS as this dedicated IAM user — the engine's
# `config/root`. Its ONLY permission is sts:AssumeRole on the bridge role: even if its long-lived
# access key leaked, it could do nothing but assume that one narrow role (requests/ PUT,
# results/ GET) — it cannot read the bucket directly, touch IAM, or reach any other resource.
#
# The access key is deliberately NOT created here, to keep a long-lived secret out of tfstate.
# After apply, mint it once by hand and hand it straight to Vault (runbook §3):
#   aws iam create-access-key --user-name mind-palace-vault --profile alberto-sso
#   vault write aws/config/root access_key=… secret_key=… region=us-east-1
# Vault can then self-rotate it with `vault write -f aws/config/rotate-root` — AWS generates the
# next key directly inside that API call and never displays it to a human; the SelfManage
# statement below (GetUser/CreateAccessKey/DeleteAccessKey) is what rotate-root needs, scoped via
# `resources` to this user's OWN arn only — it cannot touch any other IAM identity.

resource "aws_iam_user" "vault_engine" {
  name = "mind-palace-vault"
  tags = { purpose = "vault-aws-secrets-engine-config-root" }
}

data "aws_iam_policy_document" "vault_engine" {
  statement {
    sid       = "AssumeBridgeRole"
    actions   = ["sts:AssumeRole"]
    resources = [aws_iam_role.bridge.arn]
  }
  statement {
    sid       = "SelfManageForRotateRoot"
    actions   = ["iam:GetUser", "iam:CreateAccessKey", "iam:DeleteAccessKey"]
    resources = [aws_iam_user.vault_engine.arn] # self only — no other IAM identity
  }
}

resource "aws_iam_user_policy" "vault_engine" {
  name   = "assume-bridge-role"
  user   = aws_iam_user.vault_engine.name
  policy = data.aws_iam_policy_document.vault_engine.json
}

output "vault_engine_user_name" {
  description = "IAM user that Vault's AWS engine authenticates as (config/root). Mint its access key by hand (kept out of tfstate) and feed it to `vault write aws/config/root` — runbook §3."
  value       = aws_iam_user.vault_engine.name
}

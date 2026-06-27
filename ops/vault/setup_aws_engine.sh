#!/bin/sh
# Phase B — configure Vault's AWS dynamic secrets engine for the bridge role (runbook §3;
# vault-runtime-auth.md §4). The bridge gets short-lived (TTL=1h) creds minted per use instead of a
# static profile. The *fetcher* needs nothing here — it is a Lambda with its own execution role.
# (The design taxonomy's `airlock-role` has no IAM counterpart; the only assumable role is the
# bridge's, so this engine mints for exactly one role.)
#
# PREREQUISITES (owner-operated, in order):
#   1. The airlock Terraform is applied (cloud/terraform/airlock), creating the bridge role and the
#      `mind-palace-vault` engine user. Get the role ARN: terraform output -raw bridge_role_arn.
#   2. Mint the engine user's access key BY HAND (kept out of tfstate) and give it to Vault as
#      config/root (SECRET — run by hand, NOT in this script):
#        aws iam create-access-key --user-name mind-palace-vault --profile alberto-sso
#        vault secrets enable -path=aws aws            # (idempotent; this script also ensures it)
#        vault write aws/config/root access_key=<…> secret_key=<…> region=us-east-1
#
# Then run this with BRIDGE_ROLE_ARN set. Idempotent.
set -eu
: "${VAULT_ADDR:?export VAULT_ADDR=http://127.0.0.1:8200}"
: "${VAULT_TOKEN:?export VAULT_TOKEN}"
: "${BRIDGE_ROLE_ARN:?export BRIDGE_ROLE_ARN=\$(cd cloud/terraform/airlock && terraform output -raw bridge_role_arn)}"

if ! vault secrets list -format=json | grep -q '"aws/"'; then
  vault secrets enable -path=aws aws
fi

# Dynamic creds via STS AssumeRole, TTL=1h — they expire automatically (vault-runtime-auth.md §4).
# The role NAME is exactly what the bridge policy grants: aws/creds/bridge-role.
vault write aws/roles/bridge-role \
  credential_type=assumed_role \
  role_arns="$BRIDGE_ROLE_ARN" \
  default_sts_ttl=1h max_sts_ttl=1h

echo "OK: aws engine role bridge-role configured."
echo "Verify (mints a temp cred that expires in 1h): vault read aws/creds/bridge-role"

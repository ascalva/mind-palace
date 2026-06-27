# advisor — financial-data advisor agent (vault-runtime-auth.md §3). Read-only, no transaction
# scope at all (transaction capability, if it ever exists, is enforced by a broker — not by
# widening this policy). Can also see current biometric state for cross-domain advice.

path "kv/data/financial-readonly-key" {
  capabilities = ["read"]
}

path "kv/data/oura-api-token" {
  capabilities = ["read"]
}

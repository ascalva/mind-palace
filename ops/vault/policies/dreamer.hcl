# dreamer — biometric aggregates only, for the correlator's input (vault-runtime-auth.md §3).
# No AWS, no financial, no raw API tokens. An out-of-policy read is denied and logged — that
# denial is itself an alignment signal (§6), not just a security event.

path "kv/data/oura-daily-aggregates" {
  capabilities = ["read"]
}

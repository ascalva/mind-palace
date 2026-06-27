# correlator — cross-source synthesis over OBSERVED signals only (vault-runtime-auth.md §3).
# No financial, no AWS. Same biometric-aggregates grant as dreamer, kept as its own policy
# (not shared) so the two roles can diverge later without one edit touching both.

path "kv/data/oura-daily-aggregates" {
  capabilities = ["read"]
}

# gate — gate-state encryption key only (vault-runtime-auth.md §3). Read/write because the gate
# ledger key is the one secret this role actively manages, not just consumes; still nothing else.

path "kv/data/gate-ledger-key" {
  capabilities = ["read", "create", "update"]
}

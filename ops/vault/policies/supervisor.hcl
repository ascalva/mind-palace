# supervisor — token-creation authority ONLY (vault-runtime-auth.md §3). Deliberately holds no
# kv/ or aws/ read grant of its own: it mints tokens for other roles' policies, it does not read
# the secrets those tokens unlock. Mirrors the dispatcher-holds-handles-but-isn't-the-agent split.

path "auth/token/create" {
  capabilities = ["create", "update"]
}

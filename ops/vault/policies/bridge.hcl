# bridge — Zone-B research-airlock pipe (vault-runtime-auth.md §3). Dynamic AWS creds expire
# automatically (TTL=1h); the static Oura token lets it poll the API on the owner's behalf.
# The bridge has no vault (private corpus) handle regardless — this is credential scope only.

path "aws/creds/bridge-role" {
  capabilities = ["read"]
}

path "kv/data/oura-api-token" {
  capabilities = ["read"]
}

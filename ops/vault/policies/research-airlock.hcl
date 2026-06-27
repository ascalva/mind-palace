# research-airlock — the one-way research flow's own dynamic AWS role (vault-runtime-auth.md
# §3, §16). Scoped to the research S3 bucket only; distinct from bridge-role so a future
# narrowing of one never accidentally widens the other.

path "aws/creds/airlock-role" {
  capabilities = ["read"]
}

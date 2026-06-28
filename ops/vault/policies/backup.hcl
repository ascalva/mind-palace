# backup — read-only Raft snapshot capability for the scheduled backup job (BUILD-SPEC §16b).
# The unattended daily backup takes a CONSISTENT Vault snapshot via `vault operator raft snapshot
# save` (full-DR option); that needs read on this one path and nothing else. This is NOT a kv/ or
# aws/ read grant — the backup token cannot see any secret VALUE, only produce a snapshot blob
# (itself encrypted at rest by Vault's barrier, then re-encrypted by restic before it leaves).
path "sys/storage/raft/snapshot" {
  capabilities = ["read"]
}

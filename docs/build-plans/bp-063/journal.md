# Journal — bp-063 (chat sensor core: CS-1/2/3)

## 2026-07-17 — graduated (proposed), not yet started
Minted by /graduate from RATIFIED `dn-chat-sensor` CS-1 + CS-2 + CS-3 (first of the §3 tranche).
Status `proposed` — awaits the owner's `proposed → ready` blessing (owner-only, by hand).

**Grounding carried in the plan (so a fresh builder needn't re-derive):**
- Transcript JSONL shape MEASURED on a live file (§3 Q1): records typed `user`/`assistant` carry
  `message.content` blocks `text|thinking|tool_use|tool_result`; extraction keeps `text` only,
  strips the rest structurally. 105 files today (note said 103 — grew; never hard-code the count).
- OBSERVED-only store shape COPIES `core/stores/code_observations.py` (hardcoded `Provenance.OBSERVED`,
  NO provenance parameter — the structural firewall); rows must be `ObservedView`-admissible and
  `MirrorView`-refused (mirror-opacity, structural — item 1's falsifier).
- CS-1 raw-first: `RawStore.add_text` (`core/stores/rawstore.py:42`) stores verbatim BEFORE extraction;
  the on-disk transcript dir is ephemeral (CLI prunes), the rawstore is the archive.
- No reusable secret scanner exists (§3 Q5) — the guard is authored (conservative patterns), a BACKSTOP
  to the structural tool-strip; fail-closed (refuse + name the session).
- No edge handoff (§3 Q3) — reads LOCAL files, the vault-watcher species, not a zone crosser.
- `thinking` stripped in v1 (§3 Q2, parked); `active_session_id` excludes the open session (§3 Q4, parked).

**Next action when built:** item 1 (chatlog store) → item 2 (retain-raw + extract + tool-strip) →
item 3 (secret backstop + backfill + wiring; `reset_targets()` registration NAMED for the orchestrator's
post-merge step). 3-item serial. Estimate opus/200k. bp-064 (clock wiring) depends on this store.

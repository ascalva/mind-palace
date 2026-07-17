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

## 2026-07-17 — build session (builder, worktree)

Read in order: plan (full), CONSTITUTION, chat-sensor.md (full), code_observations.py (full),
provenance.py (full), rawstore.py (full), sensing.py:140-240 (ObservedView), mirror.py:60-108
(MirrorView), code_sensor.py (1-90, 250-527), config/loader.py paths, launcher.py reset_targets,
test_code_observations.py (patterns).

**Q1 JSONL shape RE-MEASURED on live files (confirms plan §3):**
- Dialogue records: top-level `type` ∈ {user, assistant}. `message.role` ∈ {user, assistant}.
- `message.content` is EITHER a bare string OR a list of blocks `{type: text|thinking|tool_use|
  tool_result, ...}`. A text block is `{"type":"text","text":"..."}`. Measured on 18cd57d7…:
  user content str(5) / list[tool_result(67), text(1)]; assistant list[thinking(47), text(17),
  tool_use(67)]. 107 transcript files on disk today.
- Extraction = `text` blocks of user/assistant ONLY; strip tool_use/tool_result (structural) +
  thinking (v1, Q2). Bare-string content ⇒ one text utterance. role→speaker: user=owner, assistant=agent.

**Wiring conventions confirmed:** rawstore shared at `cfg.paths.raw_store` (`RawStore(...)` — the
ingest/watcher convention, `core/ingest/sync.py:193`); chatlog store at
`cfg.paths.data_dir / "chatlog.sqlite"` (sibling-store convention). Transcripts dir default derives
from the CLI cwd→dir mangling (`~/.claude/projects/<mangled>`); tests inject dirs explicitly.

**reset_targets() OWED to orchestrator:** add `p.data_dir / "chatlog.sqlite"` at
`ops/lifecycle/launcher.py:592` (corpus-side wipe target; rebuilds by re-ingest from the IMMUTABLE
rawstore, which is NOT reset). I do NOT edit launcher.py — write_scope excludes it.

### Progress
- [ ] Item 1 — chatlog store (OBSERVED-only, utterance grain)
- [ ] Item 2 — sensor pipeline (verbatim retain → extract, tool-strip)
- [ ] Item 3 — secret guard + backfill + build_chat_sensor + reset_targets naming

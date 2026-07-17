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
- [x] **Item 1** — chatlog store (OBSERVED-only, utterance grain). `core/stores/chatlog.py` +
  `tests/unit/test_chatlog_store.py` (11 tests). Committed `bfb53b2`.
- [x] **Item 2 + 3** — sensor pipeline, guard, backfill, wiring. `ops/chat_sensor.py` +
  `tests/unit/test_chat_sensor.py` (30 tests total in the file). Committed <pending>.

### Item 1 notes
- `ChatUtterance` (frozen, NO provenance field) → `to_row()` hardcodes `Provenance.OBSERVED.value`.
  `ChatlogStore`: identity key (session_id, turn_index), `INSERT OR IGNORE` idempotence,
  `all_rows(provenances=…)` RowSource. `sessions()` helper for the sensor's incremental skip.
- Falsifiers pinned by test: grep-style "no provenance parameter on any public surface"; a
  source scan asserting `speaker` never co-occurs with `Provenance` (no laundering); MirrorView
  RAISES `NonMirrorRowError` over chat rows; ObservedView admits them; a hand-forged authored
  row is refused by ObservedView (the dual).

### Item 2/3 notes (why 2 and 3 landed in one commit)
The guard MUST be present the moment `sync()`/`backfill()` can store, or an intermediate commit
would ship a CS-3 (bright line #10) violation. So the fail-closed guard is authored with the
pipeline — items 2 and 3 are one logical change over the same two files. Recorded as a
deliberate grouping, not scope creep.
- **CS-1 verbatim-first:** `_ingest` retains via `rawstore.add_text(text)` BEFORE `parse_transcript`.
  `parse_transcript` computes `transcript_digest = sha256(utf-8)` matching `add_text` exactly, so
  every utterance is recoverable by construction. Test proves `rawstore.get(digest) == source_bytes`.
  Retention is UNCONDITIONAL — even a secret-refused session's raw is retained (test pins it).
- **CS-3 tool-strip:** extraction is an ALLOW-LIST — only `text` blocks of user/assistant kept;
  thinking/tool_use/tool_result + any unknown block type dropped structurally (fail-closed for
  §10 shape-changes: prose is always a `text` block). Bare-string content ⇒ one utterance.
  role→speaker: user=owner, assistant=agent (metadata, never provenance).
- **CS-3 secret guard (Q5, authored — no reusable scanner existed):** 5 high-signal patterns
  (AKIA access-key-id; named aws_secret_access_key; PEM PRIVATE KEY header; `sk-`/`sk-ant-` keys;
  keyword-bound 32+ opaque token). Fail-closed: a match REFUSES the WHOLE session (nothing stored;
  raw retained; session NAMED in `report.refused_sessions`) and raises `SecretInUtteranceError`
  with the session id — NEVER the matched value (bright line #10 second half). Whole-session
  refusal is strictly more fail-closed than per-row skip and forbids a partially-stored session.
- **DRY-RUN VALIDATION of the guard over all 107 real transcripts (no storing):** 6287 utterances,
  **3 matched, all `aws-access-key-id`, in 1 session** — genuine AWS-access-key-shaped strings
  (true positive). 106/107 sessions clean. The guard does NOT empty the corpus → the §10
  stop-and-raise ("guard false-positive-empties the corpus") does NOT fire. No finding filed.
- **Q4 active exclusion:** `active_session_id` (this build's own transcript) skipped by filename
  stem before parse; `report.skipped_active` names it. D2 full backfill default. `sync()` is the
  incremental entry (skips sessions already in `store.sessions()`); `backfill()` is D2 (all files,
  idempotent). One refused session does not abort the pass (caught per-file, named).

### OWED to the orchestrator (post-merge)
`reset_targets()` in `ops/lifecycle/launcher.py` (~:596 candidate list) must gain
`p.data_dir / "chatlog.sqlite"` as a corpus-side wipe target (rebuilds by re-ingest from the
IMMUTABLE rawstore, which is NOT a reset target — raw is sacred). NOT edited here (write_scope
excludes launcher.py — the `reference_edges.py` precedent). Also NOT done (bp-064): spine chain,
stratum registration, cut certificates. `build_chat_sensor()` is wired but NOT called by any
scheduled job — no reader, no live pass (this plan wires none).

### Gate (all 5 legs, run separately in the worktree with `--extra dev`)
- ruff check . → All checks passed
- mypy core agents eval ops scheduler scripts → Success, 212 files
- mypy (argless) → **69 errors** (== pinned baseline; my new tests added 0)
- python -m ops.type_gate → both scans OK
- pytest -q → **1497 passed, 11 skipped** (528s); new store+sensor = 41 of those

### Progress
- [x] Item 1 · [x] Item 2 · [x] Item 3 — all acceptance tests green; gate clean.

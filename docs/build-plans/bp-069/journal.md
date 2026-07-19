# Journal — bp-069 (chat real-time + lossless: growth-aware append + a live transcript watcher)

## 2026-07-18 — minted (proposed), awaiting owner bless
Owner-directed (2026-07-18), warranted by **finding-0109**. bp-068's live verification surfaced that
`sync()` FREEZES a session once ingested (bp-063 Q4), so a session left open for hours / overnight is
captured PARTIAL and its tail is lost. Owner (emphatic): unacceptable, data loss would be common, the
system is real-time so ingestion must be IMMEDIATE — parity with the code sensor (every commit → every
transcript change). This plan makes chat ingestion growth-aware + real-time. Status `proposed` — awaits
the owner's `proposed → ready` blessing (owner-only, by hand).

**Grounding carried in the plan (so a fresh builder needn't re-derive):**
- **Change detection = the rawstore `is_new` signal** (stateless, "git for transcripts"): a growth-aware
  `sync()` `add_text`s each transcript and only re-parses when `is_new` (changed); `add_batch` is
  idempotent by `(session_id, turn_index)` so re-parsing a grown file appends ONLY the new turns. No
  sidecar state store needed. Freeze-once (Q4) removed.
- **Torn-line tolerance:** `parse_transcript` (ops/chat_sensor.py:91) has a bare `json.loads` — a live
  file read mid-append can crash. Wrap per-line in try/except JSONDecodeError (skip-and-continue).
- **Watcher:** `VaultWatcher` (core/ingest/watch.py) is already a generic debounced dir-watcher
  (watchdog→poll), independent per instance. Generalize → `DirectoryWatcher` (`vault`→`path`); repoint
  the sole caller (build_vault_watcher). `build_chat_watcher` on_change → `enqueue_chat_sync`. Small
  debounce (0.5s) for immediacy.
- **Launcher:** `Components.watcher` (single) → `watchers: list`; `_serve`/`_shutdown` iterate;
  `build_components` builds vault + chat watchers. Register `chat_sync` in `router._PINNED_KINDS`.
- **Config:** a `[chat]` section (`transcripts_dir` override + watch debounce/poll) — plain fields, ratchet
  STAYS 19. Folds finding-0108's two follow-ups (G1 transcripts_dir override, G2 _PINNED_KINDS).
- **AMENDS ratified dn-chat-sensor Q4** (owner is the design authority) + notes the whole-session-refusal
  behavior under growth (a secret in a new turn freezes the session at its pre-secret state; still
  fail-closed — bright line #10 intact).

**Architecture SETTLED (owner, 2026-07-18, over several refinements):** one source (the transcript),
projected at different rates, ALL deterministic/model-free. **bp-069 = layers 0 + 1** ("the agent projects
twice"). Layer 0 = the rich dialogue (raw snapshot + tool-stripped prose), real-time, lossless. Layer 1 =
**WHAT actions were performed** — an ordered typed ACTION LOG (`owner_prompt → commit → ratify → build_plan
→ …`) extracted deterministically from the transcript's turns + TOOL RECORDS (so it reads the FULL raw
transcript, not the tool-stripped chatlog); no prose ("for prose, read layer 0"), no model. Layer 2 (=
**WHERE** they happened — deterministic edges to the exact commit/file/doc from the same tool records,
proving causation) is the SEPARATE connector agent, **bp-070**. Corrections banked in finding-0109: NO
Track-2/strata-access (reads its own transcript only), NOT the dreamer, layer 2 is causal-not-time-join. The
abstractive model summary is a LATER rate. bp-069 has no model → #10 not in play here.

**Next action when blessed:** Item 1 (growth-aware sensor + torn-line) → Item 2 (watcher + generalization
+ multi-watcher launcher + `[chat]` config). Est opus/180k, session_budget 2. ⚠️ suite stays RED-by-design
at the ratchet 19 — acceptance = only `test_core_self_containment` fails AND count == 19; verify the vault
watcher is byte-identical post-rename; verify a live transcript change re-ingests appended turns.

## 2026-07-18 (session-28, FABLE) — RE-MINTED as Phase Β: the dialogue sensor agent, born scoped
Owner sequenced "algebra leads" → the plan is rewritten under the ratified-pending `dn-agent-taxonomy`
(§2.4 sensor role, §3 Phase Β): same three items (L0 lossless growth-aware + torn-line + TOTAL
accounting; DirectoryWatcher + multi-watcher launcher; L1 action log `chat_events`), now +
`depends_on: bp-070` (consumes D2's `sensor_scope(DIALOGUE)` + conformance test), + the parity gauge
(explains the 203-files-vs-110-sessions delta), + the snapshot insurance noted
(`data/backup-staging/transcripts-snapshot-2026-07-18.tar.gz`, 203 files/60MB — tails recoverable).
Integrator renumbered bp-070→**bp-071** (bp-070 = Phase Α scope tooling). Status stays `proposed`;
bless meaningful after Α seals (or at the owner's discretion now — build order enforced by depends_on).

## 2026-07-19 (session-30, OPUS) — /build STARTED (status → in-progress); §2 manifest read
Gate passed (status was `ready`, deps bp-063/bp-068/bp-070 all complete). Worktree pointer set, contract
= builder. Read the §2 manifest in order: `ops/chat_sensor.py` (freeze-once lives in `sync()`'s
`p.stem not in known` filter, NOT in `_ingest` — so the Q4 fix is: drop that filter + gate re-parse on
rawstore `is_new`), `core/stores/rawstore.py` (`add_text -> (digest, is_new)` = the growth signal),
`core/stores/chatlog.py` (`add_batch` idempotent by `(session_id,turn_index)` — a grown re-parse appends
ONLY new turns), `core/ingest/watch.py` (`VaultWatcher` — 4 callers, all in write_scope: watch.py,
scheduler/vault_sync.py, test_vault_watcher.py, launcher.py docstring → clean rename, no alias),
`core/agent_scope.py` (D2: `sensor_scope`, `Handle`, `assert_conforms`), `core/scope.py`
(`Stratum.DIALOGUE` + DIALOGUE_TRANSCRIPT/ARTIFACT refinements; downset of DIALOGUE contains both),
`core/config/loader.py`+`config/defaults.toml` (VaultConfig is the template for `[chat]`; facade
`config/loader.py` is OUT of scope but doesn't need editing — `Config.chat` rides the already-exported
`Config`), scheduler wiring + launcher + cron.

**KEY DESIGN DECISION (Q2, resolved by grounding — no finding needed):** "freeze at pre-secret state"
is EMERGENT, not new code. Whole-session refusal stays (existing tests assert count==0 on first ingest
with a mid-session secret). Under growth: turns 0-5 land clean in pass 1 (committed, idempotent); pass 2
sees the grown file (is_new), re-parses 0-6, hits the secret at turn 6, raises → add_batch never runs
this pass → turns 0-5 STAND from pass 1. Secret never lands, earlier turns stand, raw retained. So the
secret guard logic is UNCHANGED; the Q2 behavior falls out of (idempotent prior commits + whole-session
refusal + growth-aware re-ingest). Existing whole-session tests pass verbatim.

**REPORT NAMING (reconciliation, not under-spec):** §6 pins `retained`; existing code+tests use
`transcripts_retained` (and `sessions_ingested`/`utterances_added`/`refused_sessions`/`skipped_active`).
Keeping the existing names (backward-compat, zero churn to passing tests — owner DRY) and ADDING the new
accounting buckets (`files_seen`/`sessions_grown`/`unchanged`/`empty`/`unparseable` + `is_fully_accounted`).
`transcripts_retained` IS the `retained` field.

### Item 1 DONE — L0 lossless (growth-aware + torn-line + total accounting)
**Changed:** `ops/chat_sensor.py` — (1) `parse_transcript` now torn-line tolerant (per-line
`json.loads` in try/except `JSONDecodeError` → skip+count; a bare-scalar line skipped too); factored
into `_parse_lines(text) -> ParseOutcome(utterances, decoded_records, decode_failures)` so the report
can tell `empty` (valid records, no prose) from `unparseable` (nothing decoded) — public
`parse_transcript` signature unchanged (delegates). (2) `ChatSyncReport` rewritten as TOTAL accounting:
`files_seen` + buckets `sessions_ingested`/`sessions_grown`/`unchanged`/`refused_sessions`/`empty`/
`unparseable`/`skipped_active`, with `total_accounted()` + `is_fully_accounted()` (the §2.5 parity
gauge — assertion surface AND the `__str__` log line `accounted=ok|BROKEN`). Kept legacy field names
(`transcripts_retained`/`sessions_ingested`/`utterances_added`/`refused_sessions`/`skipped_active`) —
zero churn to passing tests. (3) `_ingest(path, report, known)` now gates on rawstore `is_new`:
unchanged→`unchanged` bucket (no re-parse, no churn); grown→re-parse, `add_batch` appends only new
turns, classified `grown` vs `ingested` via `known`. (4) `sync()` DROPPED the `p.stem not in known`
filter (the freeze-once site) — processes every path, is_new gates work; `backfill()` now delegates to
`sync()` (they're identical post-growth-aware — DRY). Whole-session secret refusal UNCHANGED → Q2
freeze-at-pre-secret-state is emergent.
**Tests:** `tests/unit/test_chat_sensor.py` +6 (grown-reingests-only-new-turns, unchanged-zero-writes,
torn-trailing-line-never-raises, total-accounting-parity across all buckets, secret-in-new-turn-freezes,
+ the ChatSyncReport import); updated `test_secret_bearing_utterance_is_refused_whole` for the 3-arg
`_ingest` + fresh-rawstore so the refusal path (not the unchanged-skip) is exercised. **29 passed**
(test_chat_sensor + test_chat_sync). ruff+mypy clean. **Ratchet 19** (only ops/+tests touched).
**LIVE `palace ingest-chat`** (daemon #26 is live on OLD code — safe: SQLite WAL + INSERT OR IGNORE):
run 1 = `files=115 ingested=4 grown=1 utterances=247 retained=5 unchanged=110 accounted=ok` (the
frozen tail RECOVERED — grown=1); run 2 = `ingested=0 grown=1 utterances=0 unchanged=114 accounted=ok`
(the grown=1 is my OWN still-open session — the real-time behavior itself; the recovered sessions are
now unchanged, churn-free). Parity held live both passes.

### Item 2 NEXT — DirectoryWatcher rename + multi-watcher launcher + `[chat]` config

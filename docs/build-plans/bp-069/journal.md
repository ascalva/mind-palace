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

### Item 2 DONE — real-time trigger: DirectoryWatcher + multi-watcher launcher + `[chat]` config
**Changed:** `core/ingest/watch.py` — `VaultWatcher` → `DirectoryWatcher`, field `vault` → `path`
(pure rename; the 4 callers — watch.py, scheduler/vault_sync.py, test_vault_watcher.py, launcher.py
docstring — all repointed; NO alias, per owner rule). `scheduler/vault_sync.py` — `build_vault_watcher`
now returns `DirectoryWatcher(path=cfg.vault.path, …)` (vault behavior byte-identical). `scheduler/
chat_sync.py` — NEW `build_chat_watcher(queue, router, cfg)` (on_change → `enqueue_chat_sync`; path +
debounce/poll from `[chat]`, transcripts_dir via the sensor's resolver); `enqueue_chat_sync` now uses
`router.plan(CHAT_SYNC_KIND, priority=BACKGROUND)` (canonical, since chat_sync is now pinned).
`scheduler/router.py` — `_PINNED_KINDS |= {chat_sync, chat_events}` (finding-0108 G2). `core/config/
loader.py` + `config/defaults.toml` — NEW `[chat]` section / `ChatConfig` (transcripts_dir override
G1, watch_debounce_s=0.5, watch_poll_interval_s=5.0, events_max_per_pass=50); `Config.chat` defaulted
(direct-construction-safe). `ops/chat_sensor.py` — `build_chat_sensor` honours `cfg.chat.transcripts_dir
or _default_transcripts_dir()`. `ops/lifecycle/launcher.py` — `Components.watcher` → `watchers: list`;
`_serve` starts each, `_shutdown` stops each; `build_components` builds `[vault, chat]` watchers.
**Tests:** test_vault_watcher (DirectoryWatcher rename), test_chat_sensor_wiring (+chat-watcher enqueues
chat_sync + tier==pinned), test_lifecycle (+two-watcher start/stop; both Components updated to
`watchers=[…]`). **Full deterministic suite: 1574 passed / 4 skipped / only the ratchet red (19).**
ruff clean on all new lines (4 pre-existing E501 in launcher.py gate_cmd + test_lifecycle docstring are
finding-0105 debt, line-shifted, NOT mine — pytest node-id string, unsplittable). mypy clean.
Config ratchet STAYS 19 (`[chat]` is plain fields, no core.config first-party import).

### Item 3 DONE — L1 action log + the born scope + conformance
**New:** `core/stores/chat_events.py` — `ChatEventStore` (table `(session_id, ord)` + `chat_event_digests`
sidecar for incrementality; `replace_session` wipes+rewrites a session's log atomically; NO content
column — structural refs only, structurally). `core/chat_events.py` — `ChatEvent` + `extract_events`
(pure, model-free: reads the FULL raw JSONL — turns + tool records L0 strips; torn-line tolerant; a
two-pass parse collects tool_use_id→result so a `git commit` resolves its sha from the result bracket;
file-writes classified by path into build_plan/finding/design_note/file_edit; unknown tool → fail-open
`tool_use(name)`; `order` dense per session, `turn_index` mirrors L0's text-turn counter as the
projection-fiber backpointer) + `ChatEventProjector.project(max_sessions)` (re-extracts iff the
session's latest `transcript_digest` changed; replace-per-session) + `build_chat_event_projector`.
`ops/chat_sensor.py` — `DIALOGUE_SENSOR_SCOPE = sensor_scope(Stratum.DIALOGUE)` (born scoped).
**Wired:** `scheduler/cron.py` — `CHAT_EVENTS_KIND` + `chat_events_handler` + `enqueue_chat_events`
(pinned, BACKGROUND — the delayed rate). `scheduler/router.py` — chat_events already in `_PINNED_KINDS`
(Item 2). `ops/lifecycle/launcher.py` — handler registered, `_housekeeping` enqueues it,
`reset_targets()` += `chat_events.sqlite`; `Components.watchers: Sequence[WatcherLike]` (covariant, so
`list[DirectoryWatcher]` conforms — mypy).
**Tests:** `tests/unit/test_chat_events.py` (10): exact ordered typed sequence (prompt→response→
commit(sha)→file_edit(path)→build_plan(id)), unknown→tool_use, finding/design_note typing, torn-line,
project extract/skip-unchanged/re-extract-grown, max_per_pass cap, chat_events→pinned tier, **the D2
conformance: sensor handles ⊑ DIALOGUE_SENSOR_SCOPE + a smuggled stratum/edge-fiber handle REJECTED**.
**Full deterministic suite: 1584 passed / 4 skipped / only the ratchet red (19).** ruff+mypy clean.
**LIVE projection over real transcripts** (`build_chat_event_projector().project(max_sessions=5)`):
482 events across 5 sessions — rich typed logs (a build session: 11 commit / 24 build_plan / 57
file_edit / 1 finding; a design session: 8 design_note / 4 commit), structural refs (`bp-027`,`bp-037`),
no crash on real shapes. The extractor is validated end-to-end.

## 2026-07-19 (session-30, OPUS) — SEALED (status → complete)
**Phase Β of the diamond is done.** All 3 items built + verified in ONE OPUS session (budget was 3):
L0 growth-aware/torn-line/total-accounting (`c5d8bbf`) → real-time DirectoryWatcher + multi-watcher
launcher + `[chat]` config (`2821a53`) → L1 action log + born scope + D2 conformance (`632fa6f`).
Full deterministic suite **1584p/4s/0f**, ratchet held **19** throughout. Two live verifications on real
data: `palace ingest-chat` recovered the frozen tail (grown=1, accounted=ok, churn-free on re-run) and
`project(max_sessions=5)` produced 482 typed L1 events with structural refs. Freeze-once is gone; the
dialogue sensor now senses in real time and projects at two rates, both deterministic.

**Reconciliations (no findings needed):** kept legacy `ChatSyncReport` field names + added buckets
(zero test churn, owner DRY); Q2 "freeze at pre-secret state" is emergent (whole-session refusal +
idempotent prior commits), not new code; `ratify` kind reserved-not-emitted in v1 (design_note records
the touch — §11 parked). Pre-existing E501 debt in `launcher.py` gate_cmd (finding-0105, a pytest
node-id string) left untouched — not bp-069's concern; the deploy gate is pytest-only, not ruff.

### READ MAP (curated — the essence, ~20% of the diff)
- **The freeze-once removal (the finding-0109 fix):** `ops/chat_sensor.py:255` `sync()` — the dropped
  `p.stem not in known` filter; `ops/chat_sensor.py:213` `_ingest` — the `is_new` gate + bucket
  classification (grown vs ingested vs unchanged/empty/unparseable).
- **The parity gauge:** `ops/chat_sensor.py:176` `ChatSyncReport` — `total_accounted()` /
  `is_fully_accounted()` (the §2.5 instrument: every file → exactly one bucket).
- **The L1 extractor (the substrate bp-071 reuses):** `core/chat_events.py:135` `extract_events` —
  the turn/tool walk; `core/chat_events.py:89` `_tool_event` — the commit-sha/file-path classification
  (structural refs only).
- **The born scope + its proof:** `ops/chat_sensor.py:69` `DIALOGUE_SENSOR_SCOPE`;
  `tests/unit/test_chat_events.py` `test_the_sensor_is_born_scoped` + the two smuggled-handle rejections.
- **The DRY rename:** `core/ingest/watch.py:37` `DirectoryWatcher` (was VaultWatcher); the launcher's
  `watchers: Sequence` multi-watcher loop (`ops/lifecycle/launcher.py`).

### HANDOFF — next session (fresh OPUS)
- **Owner action any time:** `palace deploy` (unblocked since session-29) — puts the daemon (run #26,
  on OLD code) onto HEAD so real-time chat sensing + L1 projection run continuously. Run #26 is behind.
- **Phase Γ — bp-071 (integrator, `proposed`):** its Item 0 re-grounds §2/§6 against the LANDED L1
  schema (`core/chat_events.py` ChatEvent + ChatEventStore), then back to the owner for the fable bless
  gate. It consumes D1's C/DIALOGUE + D2's `integrator_scope` + reuses the tool-record parse here.
- **Phase Δ mints at Γ-seal** (bp-072→ now reserved for the cockpit; use the NEXT free id) — consumes
  D3's ComposedGraph; re-measures oq-0031 saturation over the enlarged dialogue node set.
- **Parallel papercut:** mint the cockpit plan (owner-cockpit capture) — leaf scope, owner blesses.
- Next finding **0110**.

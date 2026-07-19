---
type: build-plan
id: bp-069
alias: dialogue-sensor-agent
status: in-progress
design_ref:
  - docs/design-notes/agent-taxonomy.md            # dn-agent-taxonomy §2.4 (sensor role) + §3 Phase Β — REQUIRES RATIFICATION
  - docs/design-notes/chat-sensor.md               # RATIFIED dn-chat-sensor; Q4 amended by finding-0109
  - docs/findings/finding-0109.md                  # the owner decision (lossless + real-time) this builds
contract: builder
write_scope:
  - ops/chat_sensor.py
  - core/ingest/watch.py
  - core/chat_events.py
  - core/stores/chat_events.py
  - scheduler/chat_sync.py
  - scheduler/vault_sync.py
  - scheduler/router.py
  - scheduler/cron.py
  - ops/lifecycle/launcher.py
  - config/defaults.toml
  - core/config/**
  - tests/unit/test_chat_sensor.py
  - tests/unit/test_chat_sync.py
  - tests/unit/test_chat_events.py
  - tests/integration/test_chat_sensor_wiring.py
  - tests/integration/test_vault_watcher.py
  - tests/integration/test_lifecycle.py
session_budget: 3
cost:
  estimate:
    model: opus
    tokens: 280k
  actual: null
depends_on: [bp-063, bp-068, bp-070]
parallelizable_with: []
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0109.md
created: 2026-07-18
updated: 2026-07-19   # session-30 (opus): /build started — in-progress
re_entry: null
---

# Build Plan — Phase Β: the dialogue sensor agent (rates 0+1, born scoped, lossless + real-time)

## 0. Mode & provenance
Owner-directed (finding-0109: freeze-once is lossy — "the system is a real-time system, so ingestion
of transcripts must be immediate"; parity with the code sensor). **RE-MINTED** under the ratified
`dn-agent-taxonomy` (§2.4 sensor role, §3 Phase Β): the agent is **born scoped** — it carries its
declared scope from bp-070's D2 layer and ships its conformance test. Substance is unchanged from the
pre-taxonomy mint (three items); the language, the scope declaration, and the accounting instrument
are the re-mint. **Gates: the note ratified; bp-070 (Phase Α) sealed first.** Insurance already
taken: `data/backup-staging/transcripts-snapshot-2026-07-18.tar.gz` (203 files, 60MB) — frozen tails
recoverable regardless of CLI retention.

## 1. Objective
The **dialogue sensor agent** — one deterministic, model-free agent over the Claude Code transcripts,
projecting its own source at two rates (dn-agent-taxonomy §2.4; finding-0109):
- **L0, real-time (lossless):** growth-aware append (never freeze), torn-line tolerant, triggered by
  a live debounced watcher; raw retained content-addressed ("git for transcripts"); the deterministic
  credential scrub gates everything model-visible (bright line #10 at the layer boundary).
- **L1, delayed (the action log):** *what was performed, in order* — typed events (`owner_prompt →
  commit(sha) → file_edit(path) → build_plan(id) → ratify → …`) extracted from turns + tool records
  (the blocks L0 strips), no prose ("for prose, read L0"). The tool-record parser is the substrate
  bp-071 (the integrator) reuses.
- **Born scoped:** declared scope `Σ = {DIALOGUE↓}`, `E = ⊥`, `T = (Clock.N_S, ∗)`,
  `A = (READ, W_Σ=1, W_world=NONE)` via `core/agent_scope.sensor_scope(Stratum.DIALOGUE)`; the D2
  conformance test asserts its handle inventory ⊑ that scope.
- **Accounted:** the sync report becomes a **total accounting** (parity gauge): every file on disk is
  ingested | grown-appended | refused | empty | unparseable — none silently skipped (explains the
  203-files-vs-110-sessions delta; dn-agent-taxonomy §2.5 instruments).

## 2. Context manifest (read in order)
1. `dn-agent-taxonomy` §2.4 (the role's laws: lossless/growth-aware; scrub boundary; model-freeness
   typed) + §2.5 assumptions/instruments (source monotonicity is an ASSUMPTION — the CLI prunes;
   schema drift needs the parity ratchet).
2. `docs/findings/finding-0109.md` — the decision + the layer model (verbatim owner language).
3. `ops/chat_sensor.py` — `sync()` (freeze-skip to REMOVE), `_ingest` (retain-raw-first),
   `parse_transcript` (line 91 bare `json.loads` — no torn-line guard), `build_chat_sensor`,
   `_default_transcripts_dir`. bp-068's wiring consumed these; no duplicate builders (finding-0108).
4. `core/stores/rawstore.py` — `add_text -> (digest, is_new)`: **is_new is the change signal**
   (stateless growth detection; content-addressed snapshots). `core/stores/chatlog.py` — `add_batch`
   idempotent by `(session_id, turn_index)`; `sessions()`/`rows_for()`; rows carry
   `transcript_digest` (the projection-fiber backpointer, §2.4 of the note).
5. `core/ingest/watch.py` — `VaultWatcher`: already a generic debounced dir-watcher (watchdog→poll);
   generalize → `DirectoryWatcher` (`vault`→`path`), repoint the sole caller
   (`scheduler/vault_sync.py:build_vault_watcher`). Behavior byte-identical for vault.
6. `scheduler/chat_sync.py` (bp-068) — KIND/handler/enqueue; add `build_chat_watcher`.
   `scheduler/router.py` — `_PINNED_KINDS` gains `chat_sync` + `chat_events` (finding-0108 G2).
7. `ops/lifecycle/launcher.py` — `Components.watcher` → `watchers: list` (start/stop iterate);
   `_catchup`/`_housekeeping` enqueues; `reset_targets()` gains the chat_events store.
8. `core/config/loader.py` + `config/defaults.toml` — the `[chat]` section (plain fields; **the
   self-containment ratchet stays 19**).
9. `core/agent_scope.py` (bp-070 D2 — exists by build time) — `sensor_scope`, `assert_conforms`.

## 3. Investigation & grounding (carried from the pre-taxonomy mint; all resolved)
- **Q1 growth detection:** rawstore `is_new` — stateless, content-addressed; unchanged files skipped.
- **Q2 refusal under growth:** a secret in a NEW turn freezes the session at its pre-secret state
  (earlier turns stand; secret never lands; raw retained) — still fail-closed, recorded.
- **Q3 torn lines:** per-line `try json.loads / except skip` — a torn record re-reads complete on the
  next event; prose is a whole record, so nothing is lost.
- **Q4 debounce:** 0.5s (coalesces one turn's write; "immediate" to a human); config-sourced.
- **Q5 active_session_id:** kept but default None — we now WANT the live session, appended as it grows.
- **Q6 watcher:** generalize (a class named Vault watching chat is a DRY smell); pure rename.
- **Q7 L1 events + taxonomy:** typed events with structural refs ONLY (sha/path/id/turn — never
  verbatim content); extraction rules mind-palace-aware and grep-visible; unknown tools → generic
  `tool_use(name)` (fail-open to a RECORDED event). Incrementality by `transcript_digest` change;
  replace-per-session.
- **Q8 accounting (NEW at re-mint):** `ChatSyncReport` → total accounting over the dir listing; the
  parity gauge is an assertion surface (tests) AND a log line (ops).

## 4. Reconciliation
`ops/chat_sensor.py` growth-aware (AMENDS ratified dn-chat-sensor Q4 per finding-0109 — cite in-file);
`DirectoryWatcher` rename (vault behavior identical, covered by its test); launcher multi-watcher
(additive); `[chat]` config additive; NEW `core/chat_events.py` + `core/stores/chat_events.py`
(core-internal; ratchet unaffected); scope declaration + conformance test consume bp-070's D2 (no new
lattice machinery here).

## 5. Write scope
As front-matter. **OUT:** `core/stores/{chatlog,rawstore}.py` (consumed, not modified);
`core/agent_scope.py` + `core/scope.py` (bp-070's — consumed); the integrator (bp-071); the
abstractive model summary (typed out of the sensor — dn-agent-taxonomy §2.4c); the foundation denylist.

## 6. Interfaces pinned inline
```python
# ops/chat_sensor.py — growth-aware sync (freeze-once REMOVED):
def sync(self) -> ChatSyncReport:
    # for each *.jsonl: account it; add_text → (digest, is_new); is_new ⇒ re-parse + add_batch
    # (idempotent append by (session_id, turn_index)); guard refusal freezes at pre-secret state.
    ...
def parse_transcript(text: str) -> tuple[ChatUtterance, ...]:
    # per-line: try json.loads / except JSONDecodeError: continue   (torn-line tolerance)
    ...
DIALOGUE_SENSOR_SCOPE = sensor_scope(Stratum.DIALOGUE)     # the born scope (bp-070 D2)

# ChatSyncReport — TOTAL accounting (parity gauge):
#   files_seen / sessions_ingested / sessions_grown / utterances_added / retained /
#   refused_sessions[] / empty[] / unparseable[]        — every file lands in exactly one bucket.

# core/ingest/watch.py: class DirectoryWatcher: path: Path; on_change; debounce_s; poll_interval_s
# scheduler/chat_sync.py: build_chat_watcher(queue, router, cfg) -> DirectoryWatcher   # → enqueue_chat_sync
# scheduler/router.py: _PINNED_KINDS |= {"chat_sync", "chat_events"}

# core/chat_events.py (L1 — the action log; model-free):
@dataclass(frozen=True)
class ChatEvent:
    session_id: str; order: int; actor: str          # owner | agent
    kind: str        # prompt|response|commit|file_edit|build_plan|finding|design_note|ratify|tool_use
    ref: str         # sha | path | artifact-id | turn_index — STRUCTURAL, never verbatim content
    turn_index: int  # the projection-fiber backpointer into L0
def extract_events(session_id: str, transcript_text: str) -> list[ChatEvent]: ...   # pure
@dataclass
class ChatEventProjector:
    chatlog: ChatlogStore; rawstore: RawStore; store: ChatEventStore
    def project(self, *, max_sessions: int) -> int: ...   # re-extract iff transcript_digest changed

# core/stores/chat_events.py: ChatEventStore — (session_id, order); replace-per-session;
#   digest_for(session_id) for incrementality. data/chat_events.sqlite → reset_targets().

# scheduler/cron.py: CHAT_EVENTS_KIND + chat_events_handler + enqueue_chat_events (pinned tier,
#   BACKGROUND; housekeeping cadence — the delayed rate).

# core/config/loader.py [chat] (plain fields — ratchet stays 19):
class ChatConfig:
    transcripts_dir: Path | None = None     # override; None → _default_transcripts_dir (0108 G1)
    watch_debounce_s: float = 0.5
    watch_poll_interval_s: float = 5.0
    events_max_per_pass: int = 50
```

## 7. Items
### Item 1 — L0 lossless: growth-aware + torn-line + total accounting  (blast: sensor semantics; the Q4 amendment)
- **Acceptance:** `uv run pytest tests/unit/test_chat_sensor.py tests/unit/test_chat_sync.py -q`
  green — a session ingested-then-GROWN re-ingests ONLY the new turns; unchanged file → 0 writes
  (is_new=False); torn/garbage trailing line parses the valid records, never raises; raw retains a
  snapshot per change; the report accounts EVERY seeded file into exactly one bucket; a secret in a
  new turn freezes at pre-secret state. ruff+mypy clean; **ratchet 19**. Then a REAL re-ingest
  (`palace ingest-chat`) recovers the frozen tails from disk — verified live: grown-session count > 0
  once, 0 on the second run.
- **Falsifier:** a grown session is skipped (THE bug); a torn line crashes; unchanged files re-parse
  (churn); any file lands in no bucket (silent skip — the accounting law broken).
- **Invariant:** OBSERVED-provenance rows; append-only identity; fail-closed guard.
  **Stored data?** Yes (chatlog+raw; tests temp/in-memory; live re-ingest at the end).
  **Parallelizable?** No.

### Item 2 — the real-time trigger: DirectoryWatcher + multi-watcher launcher + config  (blast: daemon wiring + vault rename)
- **Acceptance:** `uv run pytest tests/integration/test_vault_watcher.py
  tests/integration/test_chat_sensor_wiring.py tests/integration/test_lifecycle.py -q` green — vault
  watching byte-identical post-rename; a chat-dir change enqueues `chat_sync`;
  `Router.plan("chat_sync").tier == pinned`; the lifecycle starts AND stops two watchers cleanly.
- **Falsifier:** vault watching regresses; a chat change fails to enqueue; only one watcher starts;
  shutdown errors with two watchers.
- **Invariant:** additive loop shape; local-file only. **Stored data?** Live chatlog on real runs.
  **Parallelizable?** No (after 1).

### Item 3 — L1 action log + the born scope  (blast: new store + trough job + conformance)
- **Acceptance:** `uv run pytest tests/unit/test_chat_events.py -q` green — `extract_events` over a
  seeded transcript (prompt → response → Bash `git commit`+result → `Edit` → `Write` to
  `docs/build-plans/...`) yields the EXACT ordered typed sequence (actors, refs: sha/path/plan-id);
  unknown tool → recorded `tool_use`; `project()` re-extracts iff digest changed, honours
  `events_max_per_pass`; `Router.plan("chat_events").tier == pinned`; **the D2 conformance test
  passes: the agent's handle inventory ⊑ `DIALOGUE_SENSOR_SCOPE`** and rejects a smuggled extra
  handle. Full deterministic suite green-except-the-intentional-ratchet.
- **Falsifier:** an event misordered/mistyped/dropped (esp. commit/plan-writes); verbatim content in
  a `ref`; a grown session not re-extracted (freeze-once one layer up); churn on unchanged sessions;
  the scope conformance test passes with a handle outside DIALOGUE.
- **Invariant:** model-free; reads its OWN raw via the chatlog's `transcript_digest` (projection
  fibers); refs structural only. **Stored data?** chat_events store (reset target).
  **Parallelizable?** No (after 1).

## 8. Math carried explicitly
Append-only identity `(session_id, turn_index)`; content-addressed change detection (is_new);
prefix-monotonicity is an ASSUMPTION (CLI pruning breaks it) survived by replace-per-session +
snapshots — per dn-agent-taxonomy §2.5. No other mathematical objects.

## 9. Non-goals
NO abstractive model summary (typed out of the sensor — later scoped model-client). NO integrator /
C-edges (bp-071). NO change to extraction/tool-strip/secret patterns beyond torn-line + the Q2 note.
NO edge seam. NO ratchet regression. NO removal of the housekeeping tick.

## 10. Stop-and-raise conditions
- bp-070 not sealed or `dn-agent-taxonomy` not ratified → STOP (build order).
- rawstore `is_new` fails as a growth signal → STOP, `codebase` finding (no ad-hoc sidecar state).
- The watcher rename would change vault behavior → STOP, `spec-fidelity` finding.
- The `[chat]` config would need a first-party import into core.config (ratchet ticks) → STOP.
- Any blessing: never.

## 11. Parked decisions
| Decision | Default | Re-entry |
|---|---|---|
| debounce | 0.5s | felt lag or thrash |
| refusal under growth | freeze at pre-secret state | guard precision becomes an owner concern |
| watcher class | generalize to DirectoryWatcher | rename proves risky to the vault path |
| event taxonomy breadth | the §6 kinds + generic tool_use | bp-071 needs a finer kind |

## 12. Dependency & ordering summary
`depends_on: [bp-063, bp-068, bp-070]` — Phase Β of the diamond. Items 1 → 2 → 3. **Downstream:**
bp-071 (Γ) reads L1 + reuses the tool-record parser; Δ reads the enlarged node set. Recovery: item 1's
live re-ingest + the 2026-07-18 snapshot make the frozen-tail loss fully reversible.

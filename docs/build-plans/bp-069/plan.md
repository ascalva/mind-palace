---
type: build-plan
id: bp-069
alias: chat-projection-agent-l0-l1
status: proposed
design_ref:
  - docs/design-notes/chat-sensor.md               # RATIFIED dn-chat-sensor; this AMENDS its Q4 (freeze-once)
  - docs/findings/finding-0109.md                  # the owner decision this plan builds
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
depends_on: [bp-063, bp-068]
parallelizable_with: []
supersedes: null
superseded_by: null
warrant: finding-0109
created: 2026-07-18
updated: 2026-07-18
re_entry: null
---

# Build Plan — the chat projection agent, rates 0 + 1 (real-time lossless layer 0 + delayed layer-1 action log)

## 0. Mode & provenance
Owner-directed (2026-07-18), warranted by **finding-0109**. bp-068 wired the chat sensor to RUN, and its
live verification surfaced a v1 caveat: `sync()` FREEZES a session once its id is in the store (bp-063
Q4), so a session left OPEN (hours / overnight — how the owner routinely works) is captured PARTIAL and
its tail is never ingested. The owner's standard: **parity with code ingestion** — the code sensor fires
on every commit; the chat sensor must capture every transcript change. *"The system is a real-time
system, so ingestion of transcripts must be immediate."* This plan makes chat ingestion growth-aware
(append new turns, never freeze) and real-time (a live FS watcher on the transcripts dir). It AMENDS the
ratified dn-chat-sensor Q4 (owner is the design authority; §4 records the amendment).

## 1. Objective
The chat projection agent reads its own store and emits at MULTIPLE RATES (owner, 2026-07-18: "the agent
itself reads its own store and then emits everything at its own rates"). This plan builds **rates 0 and 1**:

- **Rate 0 — real-time, lossless, deterministic (layer 0).** The transcript is loaded live and projected
  IMMEDIATELY: a changed transcript is re-parsed and its new turns APPENDED (by `(session_id, turn_index)`);
  nothing is frozen. Raw keeps versioned snapshots (content-addressed — "git for transcripts"). Reading a
  live-appended file never crashes (torn trailing line tolerated). A debounced FS watcher on the transcripts
  dir re-ingests the instant a session changes — minimal debounce, immediate. Model-free; the credential
  scrub is this rate's DETERMINISTIC gate.
- **Rate 1 — delayed EVENT SEQUENCE (layer 1), DETERMINISTIC.** At a LOWER rate (housekeeping), a MODEL-FREE
  projector emits the ORDERED LOG OF WHAT HAPPENED in each session — typed events in sequence: `owner_prompt
  → agent_response → commit(<sha>) → ratify(<artifact>) → build_plan(<id>) → finding(<id>) → …` (owner,
  2026-07-18: "a summary of the session in the correct order … no prose, but what actually happened"). NO
  prose — for the rich text, read layer 0. Events are extracted deterministically from the transcript's turns
  + TOOL RECORDS (commits, `Edit`/`Write`, writes to `docs/build-plans/` etc.), so **rate 1 reads the FULL
  raw transcript, NOT the tool-stripped chatlog** — the same tool-record substrate layer 2 (bp-070) reuses
  for its cross-artifact edges. Stored as an ordered event log per session in the agent's own store.
  Incremental: re-extract a session only when it grew. **The abstractive model-generated summary is a LATER
  rate — explicitly NOT in this plan (§9, §11); if you want prose, read layer 0.**

**The whole bp-069 agent is deterministic + model-free** (layers 0 and 1). No model touches chat here, so
#10 is not in play (the events store structural refs — shas/paths/turn-indices — never verbatim
secret-bearing content). When the later model summary lands, it will read ONLY the scrubbed store,
keeping the model-boundary = the #10 line. Structurally two cooperating components (sensor + event
projector), conceptually one multi-rate agent.

**Out of THIS plan — layer 2 (a SENSOR-UNIFICATION step, not a chat projection).** Where layers 0/1 are the
chat agent projecting its OWN transcript, layer 2 sits ABOVE the sensors and CONNECTS them: it takes the
references the transcript's TOOL RECORDS name (the `git commit` SHAs + `Edit`/`Write` file_paths + doc-path
writes, each at its exact dialogue position — the blocks layer 0 strips) and resolves them against the OTHER
sensors' stores to mint deterministic edges: chat action → the real commit → the real files → the real doc.
PROVABLE CAUSATION (owner, 2026-07-18: "we can deterministically create the links that prove causation"),
NOT a time-based join. Same shape as the existing `reference_edges` (doc↔code) extended with chat as the
causal origin — an edge-build/join, so NO dreamer/scope machinery. Its own plan (bp-070); it reuses this
plan's tool-record parser (Item 3).

Still OBSERVED-only (layer 0) / INTERPRETED (layer 1), local, secret-guarded (no bright line moves —
finding-0109).

## 2. Context manifest (read in order)
1. `docs/findings/finding-0109.md` — the decision + the owner's standard (immediacy, no loss, code parity).
2. `ops/chat_sensor.py` — `sync()` (the freeze-skip to remove), `backfill()`, `_ingest` (retain-raw-first
   → parse → guard → `add_batch`), `parse_transcript` (**line 91 bare `json.loads` — no torn-line guard**),
   `build_chat_sensor` / `_default_transcripts_dir`.
3. `core/stores/rawstore.py` — `add_text(text) -> (digest, is_new)`. **`is_new` is the change signal**:
   an unchanged transcript re-adds to nothing (is_new=False); a grown one is a new content digest
   (is_new=True). This is the stateless change-detector — no sidecar state store needed.
4. `core/stores/chatlog.py` — `add_batch` is idempotent by `(session_id, turn_index)`, so re-parsing a
   grown transcript APPENDS only the new turns. `sessions()`, `rows_for()`.
5. `core/ingest/watch.py` — `VaultWatcher`: a GENERIC debounced dir-watcher (watchdog→poll fallback);
   `observer.schedule(_Handler(), str(self.vault), recursive=True)` watches any path; each instance is
   independent (own observer/timer), so vault + chat watchers coexist. Generalize to `DirectoryWatcher`.
6. `scheduler/vault_sync.py` — `build_vault_watcher` (the pattern for `build_chat_watcher`); the sole
   real `VaultWatcher` caller (renames with the generalization).
7. `scheduler/chat_sync.py` (bp-068) — `CHAT_SYNC_KIND` / handler / `enqueue_chat_sync`; add
   `build_chat_watcher`. `scheduler/router.py` — `_PINNED_KINDS` (register `chat_sync`, folds
   finding-0108 G2).
8. `ops/lifecycle/launcher.py` — `Components.watcher` (SINGLE) + `_serve` (`c.watcher.start()`) +
   `_shutdown` (`c.watcher.stop()`) + `build_components`. Generalize to `watchers: list` for N watchers.
9. `config/defaults.toml` + `core/config/loader.py` — a `[chat]` section (watch debounce/poll +
   `transcripts_dir` override [finding-0108 G1] + layer-1 cadence/cap). Plain fields — the ratchet STAYS 19.
10. `scheduler/cron.py` — the TROUGH-JOB WIRING PATTERN (kind + handler + enqueue at housekeeping). Rate 1
    borrows only this wiring shape for `CHAT_EVENTS_KIND` — MODEL-FREE, so the pinned tier (like chat_sync),
    NOT the synthesis tier; fires on the delayed (housekeeping) cadence, not the real-time watcher.
11. `core/chat_events.py` (NEW) + `core/stores/chat_events.py` (NEW) — the rate-1 projector. To see the
    ACTIONS (commits, edits, plan-writes, ratifications) it must read the FULL raw transcript (the tool
    records layer 0 strips), NOT the tool-stripped chatlog: it fetches each session's raw blob via the
    `transcript_digest` the chatlog carries (`rawstore.get(digest)`), parses turns + tool records, and writes
    an ORDERED typed event log per session into its own store (keyed by `session_id`; a corpus-side reset
    target). No model, no other-stratum read. The tool-record parser is the substrate layer 2 (bp-070)
    reuses for its "where" edges.

## 3. Investigation & grounding
- **Q1 — how to detect growth without a state store?** The rawstore. `add_text(text)` returns
  `is_new`; a growth-aware pass reads each transcript, `add_text`s it, and only re-parses when
  `is_new` (changed). Unchanged files are skipped by content-dedup. Stateless, and it IS the
  "git for transcripts" snapshot log the owner described. RESOLVED.
- **Q2 — the whole-session-refusal invariant under growth.** Today a secret REFUSES the whole session
  (nothing stored). Under growth a session may already have earlier turns stored when a NEW turn carries
  a secret: the guard raises before `add_batch`, so the new turns don't land and earlier ones remain —
  the session freezes at its pre-secret state (secret never lands; later turns don't either until guard
  tuning). This is still fail-closed and arguably better (partial capture up to the secret). Record the
  invariant change explicitly (§4); it does not weaken bright line #10.
- **Q3 — torn trailing line.** A watcher can fire mid-append; `parse_transcript` must tolerate an
  incomplete final line (skip a line that fails `json.loads` rather than crash). Skip-and-continue per
  line (not just the last) is the robust rule — a malformed line is never a lost UTTERANCE (prose is a
  whole JSON record; a torn record is re-read complete on the next event). Debounce further reduces the
  odds. RESOLVED: tolerant per-line parse.
- **Q4 — immediacy / debounce.** watchdog gives real-time FS events; a SMALL debounce (~0.5s) coalesces
  the multi-line write of one turn without perceptible delay. Config-sourced (`[chat] watch_debounce_s`),
  overridable. Poll fallback interval config-sourced too.
- **Q5 — active_session_id.** No longer needed to EXCLUDE the live session (we now WANT to ingest + grow
  it). Keep the field (harmless; the manual verb from inside a live CLI may still pass it). Default None
  ⇒ ingest everything, append as it grows.
- **Q6 — watcher generalization vs reuse.** `VaultWatcher` is already generic; owner DRY strictness ⇒
  GENERALIZE to `DirectoryWatcher` (rename `vault`→`path`, class name) and repoint the one caller, rather
  than watch a chat dir with a class named "Vault" (a smell). Vault behavior stays byte-identical (pure
  rename); covered by `test_vault_watcher.py`.
- **Q7 (rate 1) — RESOLVED (owner, 2026-07-18): the ordered ACTION LOG ("what was performed"), model-free.**
  Layer 1 is a per-session ORDERED sequence of typed events — `owner_prompt`, `agent_response`,
  `commit(sha,msg)`, `file_edit(path)`, `build_plan(id)`, `ratify(artifact)`, `finding(id)`, … — in the order
  they occurred, extracted deterministically from the transcript's turns + tool records. NO prose ("if we
  want prose, read layer 0"), no model, no dreamer. Events carry structural REFS (sha/path/id/turn_index),
  never verbatim content. Home: a dedicated `core/stores/chat_events.py` store the agent owns. The
  abstractive model summary is a LATER rate (§9, §11).
- **Q7b (rate 1) — event taxonomy + extraction rules (deterministic).** From the raw JSONL: `owner_prompt`/
  `agent_response` from user/assistant turns; `commit` from a Bash `git commit` tool_use + its tool_result
  SHA; `file_edit` from `Edit`/`Write` tool_use (`file_path`); `build_plan`/`finding`/`design_note` from a
  `Write` whose path matches `docs/build-plans/`|`docs/findings/`|`docs/design-notes/`; `ratify` from an
  `Edit` flipping a `status:` line. Rules are mind-palace-aware and grep-visible (a §10 change is a code
  edit, not silent). Unknown tool calls → a generic `tool_use(name)` event (fail-open to a recorded event,
  never dropped).
- **Q8 (rate 1) — source + incrementality.** Reads the FULL raw transcript (tool records), fetched by the
  chatlog's `transcript_digest` per session (`rawstore.get`) — NOT the tool-stripped chatlog. Re-extract a
  session only when its `transcript_digest` changed since the last event-log row (layer 0 is growth-aware, so
  the digest changes on growth). Cap N sessions/pass (config). RESOLVED.
- **Q9 (rate 1) — no model, so #10 is not in play here.** Nothing is sent to a model; events store structural
  refs, not verbatim (secret-bearing) content. (Reading the raw is safe precisely because the reader is
  deterministic code, not a model — bright line #10 is about MODELS reading secrets.)
- **Q10 (rate 1) — cadence + tier.** Delayed rate = the housekeeping tick. MODEL-FREE ⇒ the pinned tier
  (like chat_sync — `ensure_tier` a no-op), NOT the synthesis tier. Enqueued in `_housekeeping`.
- **Q11 (rate 1) — testability.** Pure functions: raw JSONL → ordered `ChatEvent`s; tests seed a transcript
  with a prompt + a commit + an Edit + a plan-write and assert the exact event sequence. No model, no Ollama.

## 4. Reconciliation
- `ops/chat_sensor.py` — `sync()` becomes growth-aware (remove the freeze-skip; drive off rawstore
  `is_new`); `parse_transcript` gains torn-line tolerance. **AMENDS ratified dn-chat-sensor Q4** (owner
  decision, finding-0109) + the whole-session-refusal note (Q2). An in-file comment cites finding-0109.
- `core/ingest/watch.py` — `VaultWatcher` → `DirectoryWatcher` (`vault`→`path`). Generic, core-internal,
  no new import ⇒ ratchet unaffected.
- `scheduler/vault_sync.py` — repoint to `DirectoryWatcher`; behavior identical.
- `scheduler/chat_sync.py` — add `build_chat_watcher(queue, router, cfg)` (on_change → `enqueue_chat_sync`).
- `scheduler/router.py` — register `chat_sync` in `_PINNED_KINDS` (finding-0108 G2).
- `ops/lifecycle/launcher.py` — `Components.watcher` → `watchers: list`; `_serve`/`_shutdown` iterate;
  `build_components` builds both the vault + chat watchers. Additive to the loop shape.
- `config/defaults.toml` + `core/config/**` — a `[chat]` section (`transcripts_dir` override,
  `watch_debounce_s`, `watch_poll_interval_s` [rate 0] + `events_max_per_pass` [rate 1]); plain fields,
  ratchet STAYS 19 (finding-0108 G1 folded).
- `core/stores/chat_events.py` (NEW) + `core/chat_events.py` (NEW, rate 1) — the ordered-event-log store +
  the model-free projector: parses each session's raw transcript (turns + tool records) into a typed event
  sequence. NOT the dreamer. Core-internal ⇒ ratchet unaffected.
- `scheduler/cron.py` (rate 1) — add `CHAT_EVENTS_KIND` + `chat_events_handler(projector)` +
  `enqueue_chat_events` (trough kind/handler/enqueue WIRING shape only; pinned tier — model-free).
- `ops/lifecycle/launcher.py` — register the chat-events handler, enqueue it in `_housekeeping` (the delayed
  rate), and add the new event-log store to `reset_targets()` (corpus-side). Additive.

## 5. Write scope
Rate 0: `ops/chat_sensor.py` (growth-aware + torn-line), `core/ingest/watch.py` (→ DirectoryWatcher),
`scheduler/chat_sync.py` (build_chat_watcher), `scheduler/vault_sync.py` (repoint),
`scheduler/router.py` (_PINNED_KINDS), `ops/lifecycle/launcher.py` (multi-watcher + event-log wiring).
Rate 1: `core/stores/chat_events.py` + `core/chat_events.py` (NEW), `scheduler/cron.py` (CHAT_EVENTS job).
Both: `config/defaults.toml` + `core/config/**` (`[chat]`), and the six test files.
**OUT:** `core/stores/chatlog.py` + `core/stores/rawstore.py` (consumed via their public APIs, not modified);
the abstractive model-generated summary (a LATER rate); rate 2 — the "where" edges connecting actions to
commits/files/docs (the layer-2 causal connector, bp-070); the foundation denylist.

## 6. Interfaces pinned inline
```python
# ops/chat_sensor.py — growth-aware sync (drives off rawstore is_new):
def sync(self) -> ChatSyncReport:
    report = ChatSyncReport()
    for path in self._transcript_paths():
        if self.active_session_id is not None and path.stem == self.active_session_id:
            report.skipped_active = path.stem; continue
        text = path.read_text(encoding="utf-8")
        digest, is_new = self.rawstore.add_text(text)
        if not is_new:                    # unchanged since last retain → nothing new to append
            continue
        report.transcripts_retained += 1
        try:
            self._extract_guard_store(text, path.stem, report)   # parse(tolerant) → guard → add_batch
        except SecretInUtteranceError:
            continue                       # named in report.refused_sessions (Q2)
    return report

def parse_transcript(text: str) -> tuple[ChatUtterance, ...]:
    ...
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        try: record = json.loads(line)     # Q3: tolerate a torn/partial line (live append)
        except json.JSONDecodeError: continue
    ...

# core/ingest/watch.py
class DirectoryWatcher:      # was VaultWatcher; field `vault` → `path`; behavior identical
    path: Path; on_change: OnChange; debounce_s: float = 1.0; poll_interval_s: float = 5.0

# scheduler/chat_sync.py
def build_chat_watcher(queue: JobQueue, router: Router, cfg: Config) -> DirectoryWatcher:
    def _on_change() -> None: enqueue_chat_sync(queue, router)
    return DirectoryWatcher(path=<chat transcripts dir>, on_change=_on_change,
                            debounce_s=cfg.chat.watch_debounce_s,
                            poll_interval_s=cfg.chat.watch_poll_interval_s)

# scheduler/router.py
_PINNED_KINDS = frozenset({"vault_sync", "ambassador", "chat_sync"})   # finding-0108 G2

# ops/lifecycle/launcher.py
@dataclass
class Components:
    watchers: list[WatcherLike] = field(default_factory=list)   # was `watcher`; N watchers

# core/config/loader.py  (+ config/defaults.toml [chat]) — ADD, plain fields (ratchet stays 19):
@dataclass(frozen=True)
class ChatConfig:
    transcripts_dir: Path | None = None      # override; None → _default_transcripts_dir() (G1)
    watch_debounce_s: float = 0.5            # rate 0: small → immediate; coalesces one turn's write
    watch_poll_interval_s: float = 5.0
    events_max_per_pass: int = 50            # rate 1: cap sessions event-extracted per housekeeping tick

# core/chat_events.py  (NEW) — the model-free rate-1 projector: raw transcript → ordered ACTION LOG.
@dataclass(frozen=True)
class ChatEvent:
    session_id: str; order: int; actor: str      # owner | agent
    kind: str                                      # prompt|response|commit|file_edit|build_plan|ratify|finding|tool_use
    ref: str                                       # sha | path | artifact-id | turn_index (structural, never verbatim)
    turn_index: int
def extract_events(session_id: str, transcript_text: str) -> list[ChatEvent]: ...  # pure: turns+tool records → ordered events
@dataclass
class ChatEventProjector:
    chatlog: ChatlogStore; rawstore: RawStore; store: ChatEventStore
    def project(self, *, max_sessions: int) -> int:  # for each session whose transcript_digest changed:
        ...                                          #   raw = rawstore.get(chatlog digest); store.replace(extract_events(...))

# core/stores/chat_events.py  (NEW) — the agent's layer-1 store (ordered event log per session):
class ChatEventStore:                     # data/chat_events.sqlite; (session_id, order); replace-per-session
    def replace(self, session_id: str, events: list[ChatEvent], transcript_digest: str) -> None: ...
    def events_for(self, session_id: str) -> list[ChatEvent]: ...
    def digest_for(self, session_id: str) -> str | None: ...   # last-extracted transcript_digest (incrementality)

# scheduler/cron.py  (borrow dream/curate WIRING shape; pinned tier — MODEL-FREE, not synthesis):
CHAT_EVENTS_KIND = "chat_events"
def chat_events_handler(p: ChatEventProjector) -> Handler: ...   # p.project(...); logs the count
def enqueue_chat_events(queue: JobQueue, router: Router, cfg: Config) -> Job: ...  # pinned tier, background
```

## 7. Items
### Item 1 — growth-aware sensor + torn-line tolerance  (blast: sensor semantics; the ratified-Q4 amendment)
- **Objective:** `sync()` appends new turns off the rawstore `is_new` signal (freeze-once removed);
  `parse_transcript` tolerates torn lines. `build_chat_sensor` honours a `cfg.chat.transcripts_dir`
  override (G1).
- **Acceptance test:** `uv run pytest tests/unit/test_chat_sensor.py tests/unit/test_chat_sync.py -q`
  green — a session INGESTED then GROWN (more turns appended to the file) re-ingests ONLY the new turns
  (existing untouched); an unchanged session re-run adds 0 (is_new=False path); a transcript with a
  torn/garbage trailing line parses the valid records and does not raise; raw retains a new snapshot per
  change (versioned). ruff + mypy clean; **ratchet stays 19**.
- **Falsifier:** a grown session is skipped (turns lost — the whole bug); a torn line crashes the pass;
  an unchanged file re-parses/re-stores (churn); a secret in a new turn stores the secret.
- **Invariant(s):** OBSERVED-only; append-only by `(session_id, turn_index)`; fail-closed guard (Q2
  refusal note). **Touches stored data?** Yes (chatlog + raw; tests temp/in-memory). **Parallelizable?** No.

### Item 2 — the live watcher + generalization + multi-watcher launcher  (blast: daemon wiring + vault rename)
- **Objective:** `VaultWatcher`→`DirectoryWatcher` (repoint vault); `build_chat_watcher`; register
  `chat_sync` in `_PINNED_KINDS`; `Components.watchers: list` started/stopped in `_serve`/`_shutdown`;
  `build_components` builds vault + chat watchers; the `[chat]` config section.
- **Acceptance test:** `uv run pytest tests/integration/test_vault_watcher.py
  tests/integration/test_chat_sensor_wiring.py tests/integration/test_lifecycle.py -q` green — the vault
  watcher works unchanged post-rename; a chat watcher's `on_change` enqueues a `chat_sync` job; the
  lifecycle starts + stops MULTIPLE watchers; `Router(cfg).plan("chat_sync").tier == pinned` (G2). Full
  deterministic suite green-except-the-intentional-ratchet.
- **Falsifier:** the vault rename breaks vault watching; a chat change does NOT enqueue; only one watcher
  starts (chat never watched); the daemon errors on shutdown with two watchers.
- **Invariant(s):** additive loop shape (no supervisor reshape); local-file, no edge seam.
  **Touches stored data?** Yes (live chatlog on a real run). **Parallelizable?** No (after Item 1).

### Item 3 — rate 1: the deterministic per-session ACTION LOG (what happened, in order)  (blast: new model-free store + trough job)
- **Objective:** `core/stores/chat_events.py` (the ordered-event store) + `core/chat_events.py`
  (`extract_events` pure fn + `ChatEventProjector.project`) + `CHAT_EVENTS_KIND`/handler/enqueue in
  `scheduler/cron.py`, registered + enqueued at `_housekeeping` (pinned tier, model-free), + the new store in
  `reset_targets()` + `[chat] events_max_per_pass`.
- **Acceptance test:** `uv run pytest tests/unit/test_chat_events.py -q` green — `extract_events` over a
  seeded transcript (owner prompt → agent response → a `git commit` Bash call+result → an `Edit` → a `Write`
  to `docs/build-plans/bp-xxx/plan.md`) yields the EXACT ordered typed sequence with the right refs (sha,
  path, plan-id) and actors; `project()` re-extracts only sessions whose `transcript_digest` changed
  (idempotent — no-growth re-run writes 0; a grown session's log is REPLACED) and honours `max_sessions`;
  the handler runs it; `Router(cfg).plan("chat_events").tier == pinned`. ruff + mypy clean; **ratchet stays
  19**. Full deterministic suite green-except-the-intentional-ratchet.
- **Falsifier:** an event is misordered, mis-typed, or dropped (esp. a commit/plan-write — the load-bearing
  actions); verbatim/secret content lands in a `ref` (must be structural only); a grown session is NOT
  re-extracted (stale layer 1 — freeze-once one layer up); it re-extracts unchanged sessions every tick
  (churn); the job pulls a model / a non-pinned tier (it is deterministic).
- **Invariant(s):** MODEL-FREE (no Ollama); reads its own raw transcript (via the chatlog's
  `transcript_digest`) — no other stratum; refs are structural (sha/path/id/turn), never verbatim content;
  event store is corpus-side (reset target). **Touches stored data?** Yes (the event store; tests temp/
  in-memory). **Parallelizable?** No (after Item 1 — needs the growth-aware chatlog + its `transcript_digest`).

## 8. Math carried explicitly
N/A — no mathematical object. Event-driven ingest + append-only store semantics + a config section.

## 9. Non-goals
NO abstractive MODEL-generated summary — layer 1 here is the DETERMINISTIC action log ONLY; the model summary is
a later rate/refinement (owner, 2026-07-18), on the scrubbed store, its own plan. NO layer 2 (the
deterministic causal connector reading the transcript's tool records → chat↔file↔commit links — its own plan
bp-070; NOT a time-join, NOT CS-5/Track-2). NO change to the extraction/tool-strip/secret patterns (bp-063's,
beyond torn-line tolerance + the Q2 refusal note). NO edge seam (local files only). NO ratchet regression
(`[chat]` is plain fields; the event projector + watcher stay core-internal). NO removal of the housekeeping tick
(the rate-1 cadence + the rate-0 backstop).

## 10. Stop-and-raise conditions
- The rawstore `is_new` signal does not cleanly detect growth (e.g. a store that re-hashes differently) →
  STOP, file a `codebase` finding rather than bolt on a sidecar state store without grounding.
- Generalizing the watcher would change vault watching behavior (not a pure rename) → STOP: keep vault
  byte-identical, file a `spec-fidelity` finding.
- The multi-watcher launcher change reshapes the supervisor loop (not additive) → STOP (`spec-fidelity`).
- The `[chat]` config addition would require a first-party import INTO `core.config` (ticking the ratchet)
  → STOP: keep plain fields.
- Any blessing (`proposed→ready`): never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| change detection | rawstore `is_new` (stateless, git-like) | a per-session mtime/size sidecar (extra state to keep coherent; raw already is the snapshot log) | raw content-addressing changes shape |
| watcher class | generalize `VaultWatcher`→`DirectoryWatcher` | reuse `VaultWatcher(vault=chat_dir)` as-is (a "Vault" class watching chat is a DRY/clarity smell — owner-strict) | the rename proves risky to the always-on vault path |
| debounce | 0.5s (immediate; coalesces one turn) | 0s (fires per line — thrash) / vault's 1.0s (a touch slow for "immediate") | the owner feels lag or thrash |
| whole-session refusal under growth | freeze at pre-secret state (partial kept; secret never lands) | re-refuse + purge the whole session each pass (throws away good earlier turns) | guard precision becomes an owner concern |
| layer-1 fidelity | deterministic ACTION LOG now (what happened, in order; refs only) | an abstractive MODEL summary (deferred — a later rate on the scrubbed store; "for prose, read layer 0") | the owner wants prose/abstraction over the action log |
| layer-1 event source | the FULL raw transcript (tool records give commits/edits/plan-writes) | the tool-stripped chatlog (CANNOT see actions — tools are stripped) | — (chatlog structurally lacks the actions) |

## 12. Dependency & ordering summary
`depends_on: bp-063` (sensor + stores) + `bp-068` (the wiring this extends). Items serial: 1 (rate-0
growth-aware sensor — the data-model fix) → 2 (the live watcher + launcher — the real-time trigger) → 3
(rate-1 action-log projection — "what happened, in order", the delayed rate). Blast: Items 1–2
reversible/append-only + a pure vault-watcher rename; Item 3 is additive (a new projector + trough job).
**Downstream:** layers 0+1 are the chat agent's two self-projections (this plan). **Layer 2 (bp-070)** is a
different KIND of thing — a SENSOR-UNIFICATION step that connects those projections OUT to the code+commit
stratum and the docs, resolving the tool-record references into deterministic edges (`reference_edges`
shape, chat as the causal origin). It reuses this plan's Item-3 tool-record parser. Folds finding-0108's two
follow-ups (G1 transcripts_dir override, G2 _PINNED_KINDS).

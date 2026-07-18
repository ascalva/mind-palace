---
type: build-plan
id: bp-069
alias: chat-realtime-lossless
status: proposed
design_ref:
  - docs/design-notes/chat-sensor.md               # RATIFIED dn-chat-sensor; this AMENDS its Q4 (freeze-once)
  - docs/findings/finding-0109.md                  # the owner decision this plan builds
contract: builder
write_scope:
  - ops/chat_sensor.py
  - core/ingest/watch.py
  - scheduler/chat_sync.py
  - scheduler/vault_sync.py
  - scheduler/router.py
  - ops/lifecycle/launcher.py
  - config/defaults.toml
  - core/config/**
  - tests/unit/test_chat_sensor.py
  - tests/unit/test_chat_sync.py
  - tests/integration/test_chat_sensor_wiring.py
  - tests/integration/test_vault_watcher.py
  - tests/integration/test_lifecycle.py
session_budget: 2
cost:
  estimate:
    model: opus
    tokens: 180k
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

# Build Plan — real-time, lossless chat ingestion (growth-aware append + a live transcript watcher)

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
The chat sensor ingests every transcript change IMMEDIATELY and never loses a turn:
- **Growth-aware:** a changed transcript is re-parsed and its new turns APPENDED (by `(session_id,
  turn_index)`); nothing is frozen. Raw keeps versioned snapshots (content-addressed — "git for
  transcripts"). Reading a live-appended file never crashes (torn trailing line tolerated).
- **Real-time:** a debounced FS watcher on the transcripts dir (mirroring the vault watcher) re-ingests
  the instant a session changes — minimal debounce, immediate. The 6h housekeeping tick stays a backstop.
Still OBSERVED-only, local-file, model-free, secret-guarded (no bright line moves — finding-0109).

**Architecture (owner, 2026-07-18): one agent, MULTI-RATE PROJECTION.** The chat sensor is the single
model-free agent that always accepts the latest real-time transcripts and projects each layer at its own
rate: the REAL-TIME rate = raw snapshot (layer 0) + the dialogue-strata projection (cleaned utterances) —
**this plan builds that rate**; LOWER rates = layer 1 (summaries) + layer 2 (references), projected later
on their own cadence from the already-scrubbed dialogue strata (Track 2 / CS-5, hung off a periodic tick
like `dream`/`curate`). Credential removal is the agent's DETERMINISTIC gate at the real-time rate, so
every downstream (lower-rate) projection reads only scrubbed text — a model never touches a secret (bright
line #10). bp-069 is *rate 0*: the lossless real-time foundation the slower projections read.

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
   `transcripts_dir` override, folding finding-0108 G1). Plain fields — the ratchet must STAY 19.

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
  `watch_debounce_s`, `watch_poll_interval_s`); plain fields, ratchet STAYS 19 (finding-0108 G1 folded).

## 5. Write scope
`ops/chat_sensor.py` (growth-aware + torn-line), `core/ingest/watch.py` (→ DirectoryWatcher),
`scheduler/chat_sync.py` (build_chat_watcher), `scheduler/vault_sync.py` (repoint),
`scheduler/router.py` (_PINNED_KINDS), `ops/lifecycle/launcher.py` (multi-watcher), `config/defaults.toml`
+ `core/config/**` (`[chat]`), and the five test files.
**OUT:** `core/stores/chatlog.py` + `core/stores/rawstore.py` (consumed, not modified); the CS-5
correlator / layer-2 references (Track 2); the foundation denylist.

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
    watch_debounce_s: float = 0.5            # small → immediate; coalesces one turn's multi-line write
    watch_poll_interval_s: float = 5.0
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

## 8. Math carried explicitly
N/A — no mathematical object. Event-driven ingest + append-only store semantics + a config section.

## 9. Non-goals
NO CS-5 correlator / layer-2 references (Track 2, separate). NO change to the extraction/tool-strip/secret
patterns (bp-063's, beyond torn-line tolerance + the Q2 refusal note). NO edge seam (local files only).
NO ratchet regression (`[chat]` is plain fields; watcher stays core-internal). NO removal of the 6h
housekeeping tick (kept as a backstop behind the watcher).

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

## 12. Dependency & ordering summary
`depends_on: bp-063` (sensor + stores) + `bp-068` (the wiring this extends). Items serial: 1 (sensor
growth-aware — the data-model fix) → 2 (the watcher + launcher — the real-time trigger, needs the
growth-aware sync to be meaningful). Blast radius: Item 1 reversible/append-only; Item 2 renames the vault
watcher (covered by its test) + adds a second watcher. **Downstream:** lossless real-time chat is the
complete, trustworthy layer-0/1 the connectivity strata-access track (Track 2) + CS-5 layer-2 references
will read — no silent gaps. Folds finding-0108's two follow-ups (G1 transcripts_dir override, G2
_PINNED_KINDS).

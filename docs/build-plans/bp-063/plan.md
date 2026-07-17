---
type: build-plan
id: bp-063
alias: chat-sensor-core
status: proposed
design_ref:
  - docs/design-notes/chat-sensor.md            # RATIFIED — CS-1 (raw retention), CS-2 (OBSERVED), CS-3 (utterance grain + tool-strip + secret guard)
contract: builder
write_scope:
  - core/stores/chatlog.py
  - ops/chat_sensor.py
  - tests/unit/test_chatlog_store.py
  - tests/unit/test_chat_sensor.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/design-notes/recursive-strata.md                 # I1 + the parked OwnerVerdict taxonomy CS-2 defers to
  - docs/design-notes/cross-strata-dreamer.md             # RATIFIED — the correlator that will READ this stratum (CS-5)
  - docs/design-notes/global-event-clock.md               # the spine this store joins (clock wiring is bp-064, NOT here)
  - docs/findings/finding-0100.md                         # the retention chain CS-1 mirrors
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — CS-1/2/3: the chat sensor core — retain the derivation, in the observed band

## 0. Mode & provenance
Graduated from RATIFIED `dn-chat-sensor` CS-1 + CS-2 + CS-3 (the first of the note's §3 tranche;
clock wiring is bp-064, the formalization-lag instrument is triple-gated and NOT minted). Investigation
& planning produced this from a single context holding the whole note + the sibling sensor/store modules
+ a live transcript sample; implementation proceeds item-by-item on owner approval. Separate
authority-to-act from the readiness blessing (owner-only `proposed → ready`; no agent flips it).

## 1. Objective
Sense the local Claude Code session transcripts into the palace's own stores — byte-verbatim into the
immutable rawstore first, then utterance-grain extraction (owner + agent prose, tool exhaust stripped,
secret-scanned) into a new **OBSERVED-only** `chatlog` store — so the *process* of formalization
persists underneath `/capture`'s *result*, readable only in the assistant tier.

## 2. Context manifest (read in order)
1. `docs/design-notes/chat-sensor.md` — WHOLE. CS-1 (§2.1 verbatim-first, source ephemeral), CS-2
   (§2.2 everything OBSERVED, the never-automatic-promotion rule, the `promote` seam registered not
   consumed), CS-3 (§2.3 utterance grain + structural tool-strip + secret guard), §4 parked, §5 owner
   decisions D1/D2, §6 non-goals.
2. `core/stores/code_observations.py` — WHOLE. The OBSERVED-only store to COPY: hardcoded
   `Provenance.OBSERVED` (no provenance parameter anywhere — the structural firewall), `all_rows(*,
   provenances=...)` RowSource shape, `to_row()`, `open_*_store` helper, the SQLite identity-keyed
   ledger + `reset_targets()` corpus-side registration convention.
3. `core/provenance.py:44-80` — `Provenance` (OBSERVED at :61), `MIRROR_READABLE` (:78-80, excludes
   OBSERVED), the never-automatic rule (:74-77); `:128-160` the `OwnerVerdict`/`promote` stub CS-2
   registers as a consumer of (and depends on none of).
4. `core/sensing.py:148-227` — `SensedObservation` (:148) + `ObservedView` (:190, `from_observations`,
   the correlator's read boundary; `__post_init__` refuses non-observed rows). The chatlog store's rows
   must be ObservedView-admissible.
5. `core/stores/rawstore.py` — WHOLE. `add_text(text) -> (digest, is_new)` (:42), immutable, dedup by
   SHA-256 — CS-1's retention target.
6. `ops/code_sensor.py:256-527` — the sibling sensor pattern: `INTERPRETER_VERSION` (:68), the
   `@dataclass` sensor holding its handles, `sync()`/`_project()` idempotency, `backfill_observations()`
   (the deliberate-not-wired history pass), `build_code_sensor()` (:508). COPY the shape; the chat
   sensor is model-free, deterministic, no attestation-handoff-to-edge (it reads LOCAL files — see §3 Q3).
7. A live transcript: `~/.claude/projects/-Users-ascalva-mind-palace/<uuid>.jsonl` — the JSONL record
   shape (§3 Q1). Read 30–40 lines to confirm the block structure before parsing.

## 3. Investigation & grounding
- **Q1 — the transcript JSONL shape (so tool-strip is grounded, not guessed).** Each line is one JSON
  record with a top-level `type` ∈ {`user`, `assistant`, `system`, `last-prompt`, `mode`,
  `permission-mode`, `file-history-snapshot`, `attachment`, `ai-title`, `queue-operation`} plus
  `sessionId`, `timestamp`, `uuid`, `parentUuid`, `cwd`, `gitBranch`. Dialogue records carry
  `message.role` ∈ {`user`, `assistant`} and `message.content` = a list of blocks with `type` ∈
  {`text`, `thinking`, `tool_use`, `tool_result`}. (Measured on a live file: 400 lines →
  text/thinking/tool_use/tool_result = 44/43/90/90.) **Extraction keeps `text` blocks of `user`/
  `assistant` records only**; `tool_use`/`tool_result` are stripped structurally (CS-3), and `thinking`
  is stripped in v1 (see Q2). The wall `timestamp` is row metadata, never an ordering key (CS-4/Law C4).
- **Q2 — do `thinking` blocks count as utterances?** The code does not settle this — it is a design
  call the note's grain (`speaker ∈ {owner, agent}`, `text`) implicitly answers: a `thinking` block has
  no dialogue speaker (agent-internal monologue) and carries the SAME apophenia + secret risk as tool
  blocks (it quotes files, pastes /usage). **Default: strip `thinking` in v1** (utterance = a turn in the
  dialogue, not internal monologue); the formalization boundary the note targets lives in the spoken
  prose (owner questions + agent answers). Parked (§11) with re-entry = the lag instrument demonstrably
  needs the reasoning trace.
- **Q3 — does the chat sensor need the `CodeSensingHandoff` edge seam?** No. The code sensor's handoff
  (`core/sensing.py:300`) exists for the core↔edge zone boundary (commits projected across it). The chat
  sensor reads LOCAL transcript files (already on this machine, bright line #11) and writes local stores
  — the same species as the vault watcher (`core/ingest/sync.py`), not an edge crosser. **No handoff seam;
  direct store write.** (An attestation of the ingest, like the watcher's leaf, is optional — see Q6.)
- **Q4 — which session is "open"?** CS-1/CS-4 exclude open (mid-append) sessions from retention/cuts, but
  the code does not settle detection: a sensor running as an ops job cannot know from the file alone that
  the CLI has closed it. **Default: the sensor accepts an optional `active_session_id` to exclude; a
  backfill pass processes every transcript except that id (or all, if none supplied).** Cut-time exclusion
  of open sessions is bp-064's certificate concern; this plan's tooth is that a session, once ingested, is
  frozen (re-ingest of a grown open session is out of v1). Parked (§11): a robust closed-detection
  (lock/close-hook). This item's falsifier is about byte-fidelity + tool-strip, not open-detection.
- **Q5 — is there a reusable secret scanner?** No — `grep` over `core/`/`ops/` finds only keychain
  accessors (`core/factory/factory.py:69 read_secret`), no text-secret scanner. **The secret-scan guard
  is authored here**: a conservative high-signal pattern set (AWS `AKIA…`/`aws_secret_access_key`, `sk-`
  API keys, `-----BEGIN … PRIVATE KEY-----`, high-entropy 32+ char tokens near `key|token|secret|password`).
  It is a BACKSTOP; the primary defense is the structural tool-strip (Q1) — utterances rarely carry
  secrets, tool output does, and the whole block class is already gone. Fail-closed: a matching row is
  REFUSED and its session named (CS-3), never truncated-and-stored.
- **Q6 — reset semantics + attestation.** The chatlog store is corpus-side (observed stratum) → register
  in `reset_targets()` (`ops/lifecycle/launcher.py:592`) as a wipe target (rebuilds by re-ingest from the
  IMMUTABLE rawstore, which is NOT a reset target — raw is sacred). Attestation of the ingest is optional
  in v1 (the code sensor attests; the vault watcher's leaf is the precedent) — **default: no attestor
  handle in v1** to keep write_scope off `core/attestation.py`; a later wiring plan can add it. Recorded so
  its absence is a decision, not an omission.

**Additional risks surfaced:** (a) 105 files today, not 103 (the corpus grew since the note) — the
backfill count is dynamic, never hard-coded. (b) A transcript may contain a record whose `message.content`
is a bare string (older format) rather than a block list — the parser must handle both (string ⇒ one text
utterance). (c) THIS session's own transcript will be among the files — the `active_session_id` exclusion
(Q4) covers it; a self-ingest of the in-progress session is precisely the open-session case to skip.

## 4. Reconciliation
- `core/provenance.py:74-77` (the never-automatic-promotion rule) — **cross-reference-on-extension**, no
  edit: the chatlog store's module header cites this rule and CS-2, and registers the chat sensor as a
  consumer of the typed `promote`/`OwnerVerdict` seam (`:128-160`) that it depends on none of. No change
  to `provenance.py`.
- `core/stores/code_observations.py` — **cross-reference-on-extension**: `chatlog.py` copies the
  OBSERVED-only discipline (hardcoded provenance, no parameter) and says so in its header, linking the
  sibling. No edit to `code_observations.py`.
- No correction to committed code. `MirrorView.__post_init__` (`core/mirror.py:86-94`) is UNTOUCHED — its
  proof must extend to chat rows for free (they wear OBSERVED ∉ MIRROR_READABLE); item 1's falsifier
  verifies this without changing the view.

## 5. Write scope
The four files in front-matter: the new OBSERVED-only `core/stores/chatlog.py`, the new `ops/chat_sensor.py`,
their unit tests. **OUT:** `core/temporal/spine.py` (clock wiring is bp-064 — this plan writes NO chain
and registers NO stratum; the store simply exists, spine-invisible until bp-064), `core/provenance.py` /
`core/mirror.py` / `core/sensing.py` (read-only substrate — extended by cross-reference, never patched),
`core/attestation.py` (no attestor in v1, Q6), `ops/lifecycle/launcher.py` (`reset_targets()` registration
is the orchestrator's post-merge step, the `reference_edges.py` precedent — NAMED in §7 item 3, not edited
here), `config/**` (the transcript dir is a resolved default, not a config-schema change, Q4/Q1), the
correlator (its own act, CS-5), the golden set + `CONSTITUTION.md` (foundation denylist).

## 6. Interfaces pinned inline
```python
# --- CONSUMED, verbatim current signatures (do not re-derive) ---
# core/stores/rawstore.py
@dataclass
class RawStore:
    root: Path
    def add_text(self, text: str) -> tuple[str, bool]: ...   # (digest, is_new); immutable, dedup
    def get(self, digest: str) -> bytes: ...
    def exists(self, digest: str) -> bool: ...

# core/provenance.py
class Provenance(StrEnum):
    OBSERVED = "observed"                                     # ∉ MIRROR_READABLE (:78-80)
MIRROR_READABLE: frozenset[Provenance] = frozenset({Provenance.AUTHORED_SOLO, Provenance.AUTHORED_DIALOGUE})

# core/sensing.py — the correlator's read boundary the chatlog rows must satisfy
@dataclass(frozen=True)
class ObservedView:
    _rows: tuple[dict[str, Any], ...] = ()
    def __post_init__(self) -> None: ...                     # RAISES on any row provenance != "observed"
    def rows(self) -> list[dict[str, Any]]: ...

# core/stores/code_observations.py — the OBSERVED-only store shape to COPY (structure, not columns)
@dataclass
class CodeObservationStore:
    path: Path
    def add_batch(self, observations, *, interpreter, history=None) -> tuple[int, int]: ...
    def all_rows(self, *, provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]: ...
    # NB: NO method accepts a provenance value — `to_row()` hardcodes Provenance.OBSERVED.value

# --- TO BUILD ---
# core/stores/chatlog.py
INTERPRETER_VERSION = "1.0.0"          # φ_chat's worldview coordinate (the self-sensor precedent)

@dataclass(frozen=True)
class ChatUtterance:                    # one utterance-grain reading; NO provenance field
    session_id: str
    turn_index: int                    # monotonic per session, extraction order (the chain position)
    speaker: str                       # "owner" | "agent" (derived from message.role — NEVER from it to provenance)
    text: str
    transcript_digest: str             # the rawstore SHA-256 the utterance is recoverable from (CS-1)
    ts_bookmark: str                   # the wall timestamp — METADATA ONLY, never an ordering key (Law C4)
    def to_row(self) -> dict[str, Any]: ...      # {**fields, "provenance": Provenance.OBSERVED.value}

@dataclass
class ChatlogStore:                    # OBSERVED-only; identity key (session_id, turn_index)
    path: Path
    def add_batch(self, utterances: Iterable[ChatUtterance]) -> int: ...   # returns NEW rows; idempotent
    def all_rows(self, *, provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]: ...
    def rows_for(self, session_id: str) -> list[dict[str, Any]]: ...
    def count(self) -> int: ...
def open_chatlog_store(config=None) -> ChatlogStore: ...      # data/chatlog.sqlite (sibling convention)

# ops/chat_sensor.py
@dataclass
class ChatSecretGuard:                 # the fail-closed backstop (Q5)
    def scan(self, text: str) -> bool: ...        # True ⇒ a secret matched ⇒ REFUSE the row
class SecretInUtteranceError(RuntimeError): ...    # raised with the session id named (CS-3)

def parse_transcript(text: str) -> tuple[ChatUtterance, ...]: ...   # JSONL → utterances (tool/thinking stripped)

@dataclass
class ChatSensor:
    transcripts_dir: Path
    rawstore: RawStore
    store: ChatlogStore
    guard: ChatSecretGuard
    active_session_id: str | None = None           # excluded (Q4)
    def sync(self) -> ChatSyncReport: ...           # retain-raw-first, then extract, per closed session
    def backfill(self) -> ChatSyncReport: ...       # every transcript except active (D2)
def build_chat_sensor(config=None, *, active_session_id: str | None = None) -> ChatSensor: ...
```

## 7. Items
### Item 1 — the chatlog store: OBSERVED-only, utterance grain
- **Objective:** `core/stores/chatlog.py` — a SQLite store whose every row is `observed` by
  construction (no provenance parameter), identity-keyed `(session_id, turn_index)`, `all_rows` RowSource.
- **Files:** `core/stores/chatlog.py`, `tests/unit/test_chatlog_store.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_chatlog_store.py -q` green — a `ChatUtterance`
  round-trips through `add_batch`/`all_rows`; `to_row()` carries `provenance == "observed"`; `add_batch`
  is idempotent by `(session_id, turn_index)` (a re-add writes 0); `ObservedView(_rows=store.all_rows())`
  constructs, and `MirrorView(_rows=tuple(store.all_rows()))` RAISES `NonMirrorRowError` (mirror-opacity,
  structural); NO method signature in the module accepts a `Provenance`/`provenance` value (grep-asserted).
- **Falsifier:** any stored row with provenance ∉ {observed}; a `MirrorView` constructed over chat rows
  that does NOT refuse them; any code path deriving provenance from `speaker`.
- **Invariant(s):** CS-2 (everything OBSERVED, no mirror-readable mint); the DerivedStore/SensedObservation
  no-provenance-parameter discipline; identity-keyed idempotence.
- **Touches stored data?** Yes — a new SQLite table (additive; in-memory `:memory:` in tests first).
- **Parallelizable?** No (foundation for items 2–3).  **Depends on:** none.

### Item 2 — the sensor pipeline: verbatim retention first, then utterance extraction with tool-strip
- **Objective:** `ops/chat_sensor.py` reads each closed transcript, stores it byte-verbatim in the
  rawstore (CS-1), then extracts `text`-block utterances (owner + agent), stripping `tool_use`/
  `tool_result`/`thinking` structurally (CS-3), and writes them to the chatlog store.
- **Files:** `ops/chat_sensor.py`, `tests/unit/test_chat_sensor.py`.
- **Acceptance test:** unit tests green — a fixture transcript is stored in the rawstore byte-for-byte
  (`rawstore.get(digest)` equals the source bytes) BEFORE any extraction; `parse_transcript` yields only
  utterances whose text came from `text` blocks (a planted `tool_use`/`tool_result`/`thinking` block's
  content appears in NO row); `turn_index` is contiguous per session; `speaker` ∈ {owner, agent} maps
  from `message.role`; a bare-string `message.content` (legacy shape) yields one text utterance.
- **Falsifier:** tool-block or thinking-block content appearing in any extracted row (the anti-apophenia /
  hygiene tooth); a stored transcript differing byte-wise from its source; a row whose text is not
  recoverable from its `transcript_digest` in the rawstore.
- **Invariant(s):** CS-1 (raw-verbatim BEFORE derived; the source is ephemeral, the rawstore is the
  archive); CS-3 (utterance grain, tool exhaust structurally absent); model-free, deterministic.
- **Touches stored data?** Yes — rawstore (immutable) + chatlog (additive). Dry-run: tests use a tmp
  rawstore + `:memory:` chatlog; no live store path.
- **Parallelizable?** No.  **Depends on:** item 1.

### Item 3 — the secret-scan backstop + backfill + wiring
- **Objective:** the fail-closed secret guard (CS-3 hygiene backstop), `sync()`/`backfill()` over the
  transcript dir excluding the active session (Q4), `build_chat_sensor()`, and the `reset_targets()`
  registration (named for the orchestrator's post-merge step).
- **Files:** `ops/chat_sensor.py`, `tests/unit/test_chat_sensor.py`.
- **Acceptance test:** unit tests green — a planted AWS/`sk-`/private-key secret in an utterance is
  REFUSED (`SecretInUtteranceError`, session id in the message) and NEVER stored; a clean corpus of N
  fixture transcripts backfills, and a second `backfill()` writes 0 (idempotent); the `active_session_id`
  transcript is excluded; every stored row is `observed`; the report names any skipped/refused session (no
  silent cap).
- **Falsifier:** a secret-bearing utterance stored (guard bypassed); a re-run duplicating rows; the active
  session ingested; a refused row that was truncated-and-kept rather than refused-whole.
- **Invariant(s):** CS-3 (bright line #10 — a secret never enters a store; fail-closed); CS-5 (the sole
  future reader is the correlator — surfacing-only; this plan wires NO reader); D2 (full backfill default).
- **Touches stored data?** Yes — same as item 2. `reset_targets()` registration is NAMED (orchestrator
  post-merge), not edited here (write_scope excludes `ops/lifecycle/launcher.py`).
- **Parallelizable?** No.  **Depends on:** items 1–2.

## 8. Math carried explicitly
N/A — no mathematical object implemented. The sensor is deterministic parsing + content-addressed
retention; σ*/lag math is the (triple-gated) CS-6 instrument, not this plan.

## 9. Non-goals
No spine chain, no stratum registration, no cut certificate (all bp-064). No correlator sweep or any
reader (CS-5 — the sole reader is the ratified correlator, its own scoped grant). No mirror access, ever
(CS-2/CS-5, structural). No new `Provenance` class (OBSERVED exists). No dreamer/weight/confidence/
promotion/baseline coupling (I1/§15). No realtime/mid-session sensing (batch at close). No attestation
handle in v1 (Q6). No `config/` schema change (Q4). No `thinking`-block extraction (Q2, parked). No
non-Claude-Code sources (§4 parked). No transcript exfiltration — everything local (bright line #11).

## 10. Stop-and-raise conditions
- A transcript record shape not covered by Q1 (a new `message.content` block type) → journal it, handle
  the known types, SKIP + name the unknown (no silent drop); if it is load-bearing, file a `codebase`
  finding.
- The secret guard cannot be made fail-closed without false-positive-refusing legitimate prose at a rate
  that empties the corpus → STOP, file a `design` finding (the guard's precision/recall is an owner call),
  park item 3's guard with the tool-strip (item 2) still in force.
- Any pressure to mint a mirror-readable or authored chat row "because the owner wrote it" → STOP (CS-2:
  the never-automatic rule; `/capture` is the only promotion path).
- Any blessing (`proposed→ready`, `draft→ratified`): never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| `thinking`-block extraction | strip in v1 (internal monologue, not a dialogue utterance; same apophenia/secret risk as tool blocks) | extract thinking as agent utterances now (floods the store with internal reasoning; heavier hygiene surface) | the CS-6 lag instrument demonstrably needs the reasoning trace |
| open-session detection | exclude a supplied `active_session_id`; a session is frozen once ingested | robust closed-detection now (lock file / CLI close hook — no seam exists; a `core/` change out of scope) | a cut or re-ingest needs true open/closed state (bp-064 certificate work may surface it) |
| ingest attestation leaf | none in v1 (keeps write_scope off `core/attestation.py`) | attest each ingest now (the code-sensor precedent — but adds a zone + handle) | a provenance-audit consumer needs the chat-ingest attestation chain |
| `OBSERVED_DIALOGUE` refinement stratum | plain `observed`; speaker/session in row metadata | a new Stratum member now (the note forbids it for v1) | CN-4-style per-stratum stats need chat churn separated (note §4) |

## 12. Dependency & ordering summary
No upstream plan dependency — the sensor stands alone (spine-invisible until bp-064 wires its clock).
Items are strictly serial by blast radius: 1 (the OBSERVED store — schema) → 2 (read + verbatim-retain +
extract — the pipeline) → 3 (secret backstop + backfill + wiring). All writes are additive (rawstore
immutable; chatlog corpus-side). **Downstream:** bp-064 (clock wiring) registers this store's per-session
chains + the observed cut certificate; the CS-6 formalization-lag instrument (triple-gated) consumes both.
Not parallelizable with bp-064 (bp-064 imports this store) — build this first.

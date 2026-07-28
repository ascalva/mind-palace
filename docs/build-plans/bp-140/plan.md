---
type: build-plan
id: bp-140
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - ops/registry/**
  - scripts/registry.py
  - tests/unit/test_registry_store.py
  - tests/unit/test_registry_fold.py
  - tests/integration/test_registry_concurrency.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 400k
  actual: null
depends_on: []
parallelizable_with: [bp-144]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/brainstorms/the-typed-workflow-registry.md
  - core/verdict/payload.py
  - scripts/board.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — The registry store: typed events, serial minting, refs, idempotency

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27, owner hand edit). Implementation
proceeds item-by-item on owner approval. The authority to build this comes from the
note's §3 graduation license (i); the readiness blessing (`proposed → ready`) is the
owner's alone and no agent flips it.

This plan is the **first** of the registry family and changes **no enforcement
whatsoever** — the note's §3(3) says of stage (i): "closes the live ID race; changes no
enforcement." Every hook stays registered, every guard keeps its teeth, nothing is
retired. That property is what makes this plan safe to land early.

## 1. Objective

Build the append-only SQLite workflow registry — typed entities, an event log, a fold to
current state, serial ID minting, and idempotent submission — as a library plus a CLI,
live the moment it exists and enforcing nothing.

## 2. Context manifest

Read these, in order, before any work:

1. `docs/design-notes/dn-typed-workflow-registry.md` — §2.2 (entities/events/folds/refs),
   §2.8 (placement), §2.9 (invariants 1, 2, 5). The whole note is short enough to read;
   §2.2 and §2.8 are the load-bearing sections for this plan.
2. `CONVENTIONS.md` §Data stores & access — "SQLite — job queue, scheduler state, the
   propose/approve/validate gate ledger…", "Ship migrations and a `schema.md`. Keep each
   store independently replaceable." Both bind this plan.
3. `core/verdict/payload.py` — the **structural** precedent to copy: a typed payload, a
   canonical serialization with `sort_keys=True, separators=(",", ":")`, an acceptor that
   holds only the public key. This plan copies the canonicalization discipline (not the
   signing — that is bp-144).
4. `scripts/board.py:1-45` — the in-tree stance for repo-workflow tooling: a derived view,
   front-matter parsing **reused** from `.claude/hooks/_lib.py`, never re-derived.
5. `.claude/hooks/_lib.py:183-250` (`parse_front_matter`, `_scalar`, `_normalize_status`) —
   the one front-matter parser in this repo. This plan's ingest path (Item 5) reuses it.
6. `scripts/check_imports.py:1-40` + `ops/import_lint.py` — the thin-CLI-in-`scripts/`,
   library-in-`ops/` precedent this plan's layout follows (§3 Q1).
7. `docs/build-plans/bp-140/journal.md` — this plan's journal (pre-build notes).

### DRY audit — does `core/` (or the wider tree) already have this?

Required by the build-plan skill. Answers, each grounded:

- **An append-only, sequence-enforcing event store?** `core/stores/verdicts.py` is an
  append-only signed store with monotonic-seq enforcement — but it is **core**, Zone A,
  and stores *verdicts about interpretations*, not workflow artifacts. Core must not
  absorb repo-workflow tooling (`CONVENTIONS.md` §Trust boundaries: "config, eval, ops,
  agents, edge, and scheduler are all machinery built *around* core"), and the note's §2.8
  argues placement out of core explicitly. **Not reusable; do not extend it.**
- **A SQLite store idiom?** `data/queue.sqlite` (scheduler) is the in-tree SQLite idiom.
  Read it for the WAL/pragma shape if useful, but it is a job queue with leases, not an
  event log. **Pattern reuse only, no code reuse.**
- **An ID allocator?** **None exists for workflow artifacts** — verified this pass and by
  the note's §2.2: `scripts/mint_ids.py` mints *corpus note* ids via `core/ingest/mint_ids.py`
  and is unrelated to `bp-NNN` / `finding-NNNN` / `dn-` ids, which are today chosen by an
  agent eyeballing the highest existing number. This plan is the first allocator.
- **A front-matter parser?** Yes — `.claude/hooks/_lib.py:183`. **Reuse it** (Item 5), the
  way `scripts/board.py:34-38` and `scripts/handoff.py:57-61` already do. Do not write a
  second YAML subset parser; that is the exact defect finding-0101/0103 named.
- **Canonical JSON serialization?** Yes — `core/verdict/payload.py:37-42`. Copy the
  *discipline* (`json.dumps(obj, sort_keys=True, separators=(",", ":"))`); the function
  itself is verdict-specific (subject/verdict/seq/timestamp) and cannot be called for an
  event payload. This is the same "reuse the primitive, mint your own canonical form"
  judgement `core/verdict/payload.py:20-27` records for the attestation record.

## 3. Investigation & grounding

- **Q1 — where does the code live, given the note says "`scripts/`-side"?** The note §4
  says "a registry library + CLI as repo-workflow tooling (`scripts/`-side, run via
  `uv run`)". `scripts/` in this repo holds **flat single-file entry points only** —
  verified: `ls scripts/` shows no package directory, and `pyproject.toml` sets
  `explicit_package_bases = true` with the comment "scripts/ are entry points, not a
  package". A multi-module library therefore cannot live under `scripts/` without
  inventing a new layout. **The in-tree precedent for exactly this shape is
  `scripts/check_imports.py` (thin CLI, 40 lines of docstring + argument handling) over
  `ops/import_lint.py` (the library)** — `scripts/check_imports.py:31-34`. This plan
  follows it: library at `ops/registry/`, CLI at `scripts/registry.py`. Recorded as a
  parked decision (§11) so the owner can overrule at the readiness gate.
- **Q2 — may `ops/` import `core`?** Yes, and it already does in ten modules
  (`ops/effect_exec.py`, `ops/ci_witness.py`, `ops/supersede.py`, `ops/self_sensor.py`,
  `ops/code_sensor.py`, `ops/chat_sensor.py`, `ops/staging_sweep.py`, `ops/effects.py`,
  `ops/selfmod_cli.py`, `ops/lifecycle/launcher.py` — verified by grep this pass). The
  self-containment rule forbids `core → outward`, not `ops → core`; the owner's 2026-07-27
  ruling in the note's §2.4.3 states this directionality explicitly. **This plan imports no
  `core` module** (signing is bp-144's), but the placement choice is not blocked by it.
- **Q3 — does the type gate need a config change for a new `ops/` package?**
  No. `pyproject.toml [tool.mypy] files = ["core", "agents", "config", "eval", "ops",
  "scheduler", "scripts", "tests"]` already covers `ops` and `scripts`, so `ops/registry/`
  and `scripts/registry.py` land inside the Tier-2 checked region automatically. The
  Tier-2 floor is **0 errors** (`.github/workflows/ci.yml`: `uv run mypy core agents eval
  ops scheduler scripts` — "0 errors, no exceptions"), so this code must be fully typed on
  landing. No `pyproject.toml` edit is needed and none is in `write_scope`.
- **Q4 — the tests/ mypy baseline.** CI pins the whole-tree mypy count at exactly
  `MYPY_TESTS_BASELINE=69` (`.github/workflows/ci.yml`, type-gate job). New test files must
  add **zero** mypy errors or the gate goes red on a count mismatch. Write the tests typed.
- **Q5 — what is the exact store filename?** The note parks it ("exact store filename /
  snapshot format — decided at stage (i) build"). This plan **decides it** (§6):
  `~/.mind-palace/registry.sqlite`, overridable by `OUROBOROS_REGISTRY`.
- **Q6 — which entity types exist?** The note §2.2 names four: design note, build plan,
  finding, journal entry. The repo also carries **deskcheck records** (`_lib.py:383`
  `is_deskcheck`, `scripts/board.py:283` `_scan_deskchecks`) and **owner questions**
  (`scripts/board.py:219` `scan_oqs`), both of which carry `track:` and a state. **The
  code does not settle whether these are registry entities**; the note does not name them.
  Parked (§11) with a recorded default: the schema's `entity_type` is a free string
  validated against a **registry-owned table**, so adding a type later is a data change,
  not a schema migration. Do not silently invent state machines for them.
- **Q7 — is `~/.mind-palace/` already in use?** Yes — the exhaust lane lives at
  `~/.mind-palace/exhaust/reports/` (memory: phone build report). A sibling file in the
  same machine-level directory is consistent with existing practice and satisfies the
  note's §2.8 "outside the repo, not `data/`" requirement (each worktree has its own
  `data/`; a per-worktree store would defeat serial minting).

**Additional risks or questions surfaced during reading:**

- SQLite `AUTOINCREMENT` on the events table gives a monotonic `seq` that is never reused
  even after a delete — but nothing is ever deleted here (invariant 1), so the guarantee is
  belt-and-braces. Keep it: it makes a gap in the sequence a detectable anomaly, the same
  reasoning `core/verdict/payload.py:58` records ("a gap is censorship, detectable").
- The note's invariant 5 ("reads degrade to the export; they never wait on a writer") is
  only half-satisfiable in this plan: the export does not exist until bp-142. This plan
  delivers the *substrate* half (WAL + `busy_timeout`, so a read never waits on a writer);
  the *fallback* half is bp-141/bp-142. Say so in the journal; do not claim invariant 5 is
  discharged here.

## 4. Reconciliation

- `docs/design-notes/dn-typed-workflow-registry.md` §4 — "a registry library + CLI as
  repo-workflow tooling (`scripts/`-side…)" → **cross-ref: extension**. This plan reads
  "scripts/-side" as *the CLI surface is scripts-side*, and places the library in `ops/`
  following `scripts/check_imports.py` → `ops/import_lint.py`. This is an extension of the
  note's placement decision to a layout the note did not specify, **not** a correction of
  it: the note's operative constraints (repo-workflow tooling, not core, not the daemon,
  run via `uv run`) are all honored. Recorded in §11; the owner may overrule at the
  readiness gate. **The design note is not edited by this plan** (it is ratified and
  agent-immutable).
- `docs/design-notes/dn-typed-workflow-registry.md` §4 — "**never** importing `core` unless
  the owner rules otherwise per §2.4.3" → **cross-ref: extension**, no action here. The
  owner *did* rule otherwise (§2.4.3's ⚑⚑ block, 2026-07-27), and this plan imports no
  `core` anyway. Noted so a later reader does not treat §4's clause as live.
- `CONVENTIONS.md` §Data stores & access — "Ship migrations and a `schema.md`" →
  **cross-ref: extension**. Item 1 ships `ops/registry/schema.md` and a `schema_version`
  row, honoring the convention rather than correcting it.

## 5. Write scope

- `ops/registry/**` — the library: `__init__.py`, `store.py` (connection + pragmas +
  migration), `events.py` (typed event + canonical payload), `ids.py` (serial minting),
  `fold.py` (state projection + query), `schema.md` (the required store documentation).
- `scripts/registry.py` — the thin CLI (`mint`, `submit`, `query`, `events`), following
  `scripts/check_imports.py`'s shape: argument handling and printing, no logic.
- `tests/unit/test_registry_store.py` — schema, pragmas, migration, idempotency.
- `tests/unit/test_registry_fold.py` — the fold and the query surface.
- `tests/integration/test_registry_concurrency.py` — the F1 parallel-minting proof.

**Deliberately OUT of scope:** every hook and `.claude/settings.json` (this plan retires
nothing); `pyproject.toml` (no dependency and no mypy-config change is needed — §3 Q3);
`docs/design-notes/**` (ratified, agent-immutable, and on no account edited);
`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py` (foundation denylist, never
writable); every existing artifact's front matter (migration is bp-143); `scripts/board.py`
and `scripts/handoff.py` (re-pointing them is bp-148); `docs/tracks/workflow.md` (the
track manifest's `dod` is the orchestrator's to update, not a builder's).

**Retrofit check:** this plan changes no existing symbol, so no existing test asserts a
surface it moves. `grep -rn "registry" tests/` before starting to confirm no name collision
with an existing test module; if one exists, report it rather than renaming someone
else's file.

## 6. Interfaces pinned inline

Copy these verbatim; do not infer any of it from the note.

### 6.1 Store location and pragmas

```python
# ops/registry/store.py
DEFAULT_PATH = Path.home() / ".mind-palace" / "registry.sqlite"
ENV_OVERRIDE = "OUROBOROS_REGISTRY"   # tests and drills point this at a scratch file

PRAGMAS = (
    "PRAGMA journal_mode=WAL",        # note §2.8: readers do not block the writer
    "PRAGMA synchronous=NORMAL",
    "PRAGMA busy_timeout=5000",       # note §2.9(1): a read never fails closed on a lock
    "PRAGMA foreign_keys=ON",
)
```

WAL is the substrate the note's §2.8 names, quoted from SQLite's own documentation:
"WAL provides more concurrency as readers do not block writers and a writer does not block
readers." Write serialization (one writer at a time) **is** the serial-minting property,
obtained from the substrate rather than built.

### 6.2 Schema (DDL, verbatim)

```sql
CREATE TABLE IF NOT EXISTS events (
  seq              INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id        TEXT NOT NULL,
  entity_type      TEXT NOT NULL,
  kind             TEXT NOT NULL,
  payload          TEXT NOT NULL,          -- canonical JSON, sort_keys, (",",":")
  idempotency_key  TEXT NOT NULL UNIQUE,   -- invariant 2 lives on this UNIQUE
  actor            TEXT NOT NULL,          -- session/agent label, never a secret
  recorded_at      TEXT NOT NULL,          -- ISO-8601 UTC; DATA, not a render input
  signature        TEXT,                   -- NULL until bp-144/bp-145; never dropped
  signer           TEXT
);
CREATE INDEX IF NOT EXISTS events_entity ON events(entity_id, seq);
CREATE INDEX IF NOT EXISTS events_kind   ON events(kind, seq);

CREATE TABLE IF NOT EXISTS ids (
  entity_type  TEXT    NOT NULL,
  number       INTEGER NOT NULL,
  entity_id    TEXT    NOT NULL UNIQUE,
  PRIMARY KEY (entity_type, number)
);

CREATE TABLE IF NOT EXISTS entity_types (
  entity_type  TEXT PRIMARY KEY,
  ref_format   TEXT NOT NULL              -- e.g. 'bp-{n:03d}', 'finding-{n:04d}'
);

CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
```

`signature`/`signer` are nullable from day one so bp-145 adds no migration to the events
table — the column exists, unused, and the note's invariant 1 ("no event is ever mutated")
is never at risk from a later `ALTER`.

### 6.3 Event kinds — the closed set (note §2.2, verbatim)

```
minted | transitioned | related | content-landed | parked | sealed
```

`content-landed` records a **prose revision as a content hash** — the prose itself stays in
the file. Nothing else is added in this plan; a new kind is a design change, not a build
decision.

### 6.4 Ref formats

```python
REF_FORMATS = {
    "design-note":  "dn-{slug}",        # slug-keyed, not numbered
    "build-plan":   "bp-{n:03d}",
    "finding":      "finding-{n:04d}",
    "journal-entry": "{plan_ref}#{n:04d}",
}
```

Grounded in the tree as it stands: `docs/build-plans/bp-140/`, `docs/findings/finding-0269.md`,
`docs/design-notes/dn-typed-workflow-registry.md`.

### 6.5 The library API

```python
# ops/registry/__init__.py
def open_registry(path: Path | None = None) -> Registry: ...

class Registry:
    def mint(self, entity_type: str, *, idempotency_key: str, payload: dict[str, object],
             actor: str) -> str:
        """Allocate the next serial id for `entity_type`, append the `minted` event, and
        return the ref. ATOMIC: the number allocation and the event insert share one
        BEGIN IMMEDIATE transaction, so two concurrent callers cannot receive the same ref
        (note §2.2, falsifier F1). Re-submitting the SAME idempotency_key returns the SAME
        ref and appends nothing (invariant 2)."""

    def submit(self, event: Event) -> int:
        """Append one event; return its seq. Idempotent on event.idempotency_key."""

    def fold(self, entity_id: str) -> EntityState:
        """Current state as a fold over the entity's events, oldest first."""

    def query(self, *, entity_type: str | None = None, status: str | None = None,
              track: str | None = None) -> list[EntityState]: ...

    def events(self, entity_id: str | None = None) -> list[Event]: ...
```

```python
@dataclass(frozen=True)
class Event:
    entity_id: str
    entity_type: str
    kind: str                       # one of §6.3
    payload: dict[str, object]
    idempotency_key: str
    actor: str
    recorded_at: str                # ISO-8601 UTC
    signature: str | None = None
    signer: str | None = None

    def canonical(self) -> bytes:
        """The deterministic bytes of the payload — the same discipline as
        core/verdict/payload.py:37-42, which this repo already trusts:
            json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
        Reproducible across processes and versions; the byte string a signature will
        later cover (bp-144)."""
```

```python
@dataclass(frozen=True)
class EntityState:
    entity_id: str
    entity_type: str
    status: str | None              # last `transitioned`.to_status, else `minted`.status
    relations: dict[str, list[str]] # design_ref, depends_on, links, supersedes, warrant…
    fields: dict[str, object]       # track, contract, write_scope, cost, …
    content_hash: str | None        # last `content-landed`.content_hash
    last_seq: int
```

### 6.6 The fold rule (pinned, so two implementations cannot disagree)

Events for an entity are applied **in ascending `seq`**:

- `minted` — seeds `entity_type`, `fields`, `relations`, and `status` from the payload.
- `transitioned` — sets `status = payload["to_status"]`. A `transitioned` whose
  `payload["from_status"]` does not equal the current folded status is **accepted and
  recorded** (invariant 1: nothing is mutated or rejected retroactively) but surfaces in
  `query()` output as a `conflict` marker. It is never silently dropped.
- `related` — appends to `relations[payload["relation"]]`; duplicate edges collapse.
- `content-landed` — sets `content_hash`.
- `parked` — sets `status = "parked"` and requires `payload["re_entry"]` to be a non-empty
  string; a `parked` without it is **rejected at submission** (the greppable
  "parked ⇒ re-entry" gate, `agent-workflow.md` §3 Principle 1, upgraded to schema).
- `sealed` — sets `status = "complete"`; its typed follow-through fields are bp-147's
  concern, not this plan's. Accept and store the payload as given.

### 6.7 CLI surface

```
uv run scripts/registry.py mint <entity-type> --key <uuid> --field k=v ...   # prints the ref
uv run scripts/registry.py submit --file <event.json>                        # prints the seq
uv run scripts/registry.py query [--type T] [--status S] [--track T]         # one row per line
uv run scripts/registry.py events [<ref>] [--json]
uv run scripts/registry.py doctor                                            # store path, schema version, counts
```

Every subcommand exits 0 on success, 2 on usage error, 1 on a store error — the
`scripts/check_imports.py` exit-code idiom.

### 6.8 The invariants this plan must satisfy (note §2.9, verbatim)

1. No event is ever mutated or deleted; corrections are events.
2. Two submissions with one idempotency key yield one ref, always.
5. Reads … never wait on a writer and never fail closed. *(substrate half only — see §3.)*
9. The registry holds no secret: not the MFA secret (oq-0037, parked), not key material —
   public keys and signatures only (NN-10).

## 7. Items

### Item 1 — the store: schema, pragmas, migration, `schema.md`

- **Objective:** a WAL-mode SQLite store that opens, migrates to version 1, and documents
  itself.
- **Files:** `ops/registry/__init__.py`, `ops/registry/store.py`, `ops/registry/schema.md`,
  `tests/unit/test_registry_store.py`
- **Acceptance test:** `uv run pytest tests/unit/test_registry_store.py -q` green, with a
  test that opens a scratch store via `OUROBOROS_REGISTRY`, asserts
  `PRAGMA journal_mode` returns `wal`, asserts `schema_version` is 1, and asserts a second
  `open_registry()` on the same file is a no-op (idempotent migration).
- **Falsifier:** the store opens in `delete` journal mode on the owner's machine (e.g. the
  file lives on a filesystem where WAL is unavailable, or the connection is opened
  read-only) — WAL is the whole concurrency argument of §2.8, so a silent fallback voids
  it. Assert the mode; do not assume it.
- **Invariant(s) it must not violate:** invariant 9 — no secret, no key material, ever
  written to this store.
- **Touches stored data?** No — it creates a NEW store at a NEW path. It must never open
  `data/*.sqlite`.
- **Parallelizable?** No.  **Depends on:** none.

### Item 2 — the typed event and its canonical payload

- **Objective:** `Event` with the closed kind set and a canonical byte encoding.
- **Files:** `ops/registry/events.py`, `tests/unit/test_registry_store.py`
- **Acceptance test:** a test asserts `Event.canonical()` is byte-identical for two
  differently-ordered but equal payload dicts, and that an unknown `kind` raises
  `ValueError` at construction.
- **Falsifier:** `canonical()` output differs across two Python processes for the same
  payload (e.g. because a `set` or a `float` leaked into the payload). Run the encoding in
  a subprocess and compare bytes — if it differs, the encoding cannot carry a signature
  later (bp-144) and the design of the payload is wrong.
- **Invariant(s) it must not violate:** invariant 1 — `Event` is frozen; no setter exists.
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** Item 1.

### Item 3 — serial minting, atomic

- **Objective:** `mint()` allocates the next number for an entity type inside one
  `BEGIN IMMEDIATE` transaction and returns the formatted ref.
- **Files:** `ops/registry/ids.py`, `ops/registry/store.py`,
  `tests/unit/test_registry_store.py`
- **Acceptance test:** a test mints 50 findings sequentially and asserts the refs are
  `finding-0001` … `finding-0050` with no gaps and no repeats.
- **Falsifier:** the allocation reads `MAX(number)` outside the write transaction (the
  read-then-write race). Prove it is inside by asserting that a mint against a store whose
  write lock is held by another connection **blocks and then succeeds**, rather than
  returning a duplicate.
- **Invariant(s) it must not violate:** invariant 1; the `ids` UNIQUE constraint on
  `entity_id` must be the last line of defence, never the first.
- **Touches stored data?** Yes (the registry's own store). Dry-run: `doctor` prints the
  next number for each type without allocating; run it before and after.
- **Parallelizable?** No.  **Depends on:** Items 1, 2.

### Item 4 — idempotent submission

- **Objective:** two submissions carrying one idempotency key yield one event and one ref.
- **Files:** `ops/registry/store.py`, `tests/unit/test_registry_store.py`
- **Acceptance test:** a test submits the same `Event` twice and asserts (a) `events()`
  returns one row, (b) both calls return the same seq, (c) `mint()` called twice with one
  key returns the same ref and allocates one number.
- **Falsifier:** the second submit raises `sqlite3.IntegrityError` instead of returning the
  existing ref. A retry after a timeout is the *designed* path (note §2.2); an exception
  there means the degraded mode (bp-141) can never reconcile and invariant 2 is not met.
- **Invariant(s) it must not violate:** invariant 2, verbatim.
- **Touches stored data?** Yes (registry store only).
- **Parallelizable?** No.  **Depends on:** Item 3.

### Item 5 — the fold and the query surface

- **Objective:** `fold()` projects an entity's events to `EntityState` per §6.6; `query()`
  filters by type/status/track.
- **Files:** `ops/registry/fold.py`, `tests/unit/test_registry_fold.py`
- **Acceptance test:** `uv run pytest tests/unit/test_registry_fold.py -q` green, covering
  each of the six event kinds, the `parked`-without-`re_entry` rejection, and the
  out-of-order `transitioned` conflict marker.
- **Falsifier:** the fold's answer depends on insertion order rather than `seq` order —
  demonstrate by inserting events with interleaved seqs and asserting the same result.
  If it differs, "current state is a fold over the log" (note §2.2) is not true of this
  implementation.
- **Invariant(s) it must not violate:** the fold is **pure** — it never writes. Assert the
  store is opened read-only for `fold()`/`query()` in at least one test.
- **Touches stored data?** No (read path).
- **Parallelizable?** Yes.  **Depends on:** Item 2.

### Item 6 — the CLI, and the F1 concurrency proof

- **Objective:** `scripts/registry.py` exposes §6.7, and two genuinely parallel processes
  minting concurrently never collide.
- **Files:** `scripts/registry.py`, `tests/integration/test_registry_concurrency.py`
- **Acceptance test:** `uv run pytest tests/integration/test_registry_concurrency.py -q`
  green: N ≥ 8 **subprocesses** (not threads — the note's scenario is parallel worktree
  builders, i.e. separate processes) each mint 20 findings against one scratch store;
  assert 160 distinct refs, no gaps, no duplicates. Plus `uv run scripts/registry.py doctor`
  exits 0.
- **Falsifier:** **F1 (serial minting)** — any duplicate ref across the subprocesses, or a
  timed-out-and-retried submit yielding two refs. Either observation voids §2.2's central
  claim and this plan does not land.
- **Invariant(s) it must not violate:** invariants 1, 2, 9.
- **Touches stored data?** Yes (scratch store via `OUROBOROS_REGISTRY`; the test must
  **never** touch `~/.mind-palace/registry.sqlite` — assert the env var is set in the test's
  own setup and fail the test if it is not).
- **Parallelizable?** No.  **Depends on:** Items 3, 4, 5.

## 8. Math carried explicitly

N/A — no mathematical object implemented. The fold is a left fold over a totally ordered
event sequence, which is a data-structure operation, not a mathematical object earning a
field-guide entry; its correctness obligation is Item 5's acceptance and falsifier.

## 9. Non-goals

- **No enforcement change.** No hook is edited, removed, or weakened. `.claude/settings.json`
  is untouched. Stage (i) "changes no enforcement" (note §3(3)).
- **No export, no ratchet, no migration.** Rendering front matter back into files is bp-142;
  backfilling existing artifacts is bp-143. This plan's store starts **empty**.
- **No signing.** `signature`/`signer` columns exist and stay NULL; bp-144 builds the
  primitive, bp-145 wires admission.
- **No degraded mode.** The pending file, provisional refs, reconcile, and recovery import
  are bp-141.
- **No `land` subcommand, no admission checks.** bp-146.
- **No consumer re-pointing.** `scripts/board.py`, `scripts/handoff.py`, and every skill
  keep reading the file tree. bp-148.
- **No new dependency.** `sqlite3` is stdlib; `pyproject.toml` is not edited.
- **No state machine invented for deskcheck records or owner questions** (§3 Q6).

## 10. Stop-and-raise conditions

- The owner overrules the `ops/registry/` + `scripts/registry.py` layout (§3 Q1, §11 row 1)
  — park the affected items with the re-entry condition and continue with the ones whose
  files do not move.
- WAL cannot be enabled at the chosen path (Item 1's falsifier) — **stop**: §2.8's
  concurrency argument rests on it. File a `spec-defect` finding naming the observed
  journal mode and the filesystem.
- F1 trips (Item 6) — **stop**. Serial minting is the whole reason stage (i) exists.
- A test is discovered that would need a file outside `write_scope` to pass — file a
  finding and stop; never route around `scope-guard`.
- Any temptation to touch `.claude/settings.json` or a hook — stop; that is bp-149's
  blocked territory and requires owner amendments to two ratified notes.
- A blessing this plan would have to perform (`proposed → ready` on itself, or any status
  flip on a design note) — it must not; surface it instead.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Library placement | `ops/registry/` library + `scripts/registry.py` CLI, per the `ops/import_lint.py` ↔ `scripts/check_imports.py` precedent | (a) a package under `scripts/` — `pyproject.toml` declares scripts are entry points, not a package, and `explicit_package_bases` would need re-reasoning; (b) `core/registry/` — forbidden by note §2.8 and CONVENTIONS §Trust boundaries | Owner overrules at the `proposed → ready` gate; prerequisite: the owner's reading of note §4's "scripts/-side" |
| Store filename | `~/.mind-palace/registry.sqlite`, env override `OUROBOROS_REGISTRY` | a dotfile in `$XDG_DATA_HOME` — the repo already uses `~/.mind-palace/` for the exhaust lane, so a second convention would fragment the machine-level surface | Owner names a different path; prerequisite: none (one-line change) |
| Are deskcheck records and owner questions registry entities? | **No** for now; `entity_types` is a data table so adding one later is an INSERT, not a migration | modelling them now — the note names four entity types and inventing two more state machines is exactly the "infer design" defect graduation exists to prevent | The owner rules, or a later plan graduates a note that names them; prerequisite: an owner ruling |
| Snapshot/export format | Not decided here | deciding it now would pre-empt bp-142, which owns the idempotence pin | bp-142 |
| Batch signature over a set of transitions | Not built (note's own parked row) | — | owner hits the per-touch friction on a real batch |

## 12. Dependency & ordering summary

**Within the plan.** Item 1 → Item 2 → Item 3 → Item 4 → Item 6; Item 5 depends on Item 2
and may proceed in parallel with Items 3–4. Blast-radius phase order is respected: Items 1,
2 and 5 are read-only or pure (no store mutation beyond schema creation); Items 3, 4 and 6
write to the registry's **own** store and nothing else; **no item in this plan writes to an
existing repo artifact, an existing store, or any enforcement surface** — that is the whole
reason stage (i) lands first.

**Across plans.** This plan is the root of the registry family:
`bp-140 → {bp-141, bp-142, bp-146}`; `bp-142 → bp-143`; `bp-145` needs `bp-140` and
`bp-144`. `bp-144` (the signing primitive) has **no dependency on this plan** — note §2.5.2:
"key onboarding does not block on the registry … the signing primitive works against today's
markdown+git world" — and its `write_scope` (`ops/transition_sig.py`, `ops/transition_keys/**`,
`scripts/sign_transition.py`) is disjoint from this one's, so the two may run concurrently.
`bp-138`/`bp-139` (autopilot AP5/AP6) are declared independent of this entire family by the
note's §3(5): "nothing here blocks them and they block nothing here."

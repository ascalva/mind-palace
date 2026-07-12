---
type: build-plan
id: bp-018
status: in-progress
design_ref:
  - docs/design-notes/self-sensing.md # B-a; §2.2 versioned re-interpretation, §2.4 mechanism gap, §2.5 reset ruling, V2
contract: builder
write_scope:
  - "core/stores/code_observations.py"
  - "core/stores/observation_history.py"
  - "ops/code_sensor.py"
  - "ops/lifecycle/launcher.py" # ONE tuple entry in _RESET_GUARD (+ its comment) — the oq-0013/bp-012 grant precedent; nothing else in this file
  - "tests/unit/test_code_observations.py"
  - "tests/unit/test_code_sensor.py"
  - "tests/unit/test_observation_history.py"
  - "tests/unit/test_interpreter_versions.py"
  - "docs/build-plans/bp-018/**"
  - "docs/findings/**"
session_budget: 1
cost:
  estimate: { model: fable, tokens: 250k } # core-store invariants + the reset path: the falsifier needs judgment (supersession semantics), not just green tests
  actual: null
depends_on: []
parallelizable_with: [bp-021, bp-022] # disjoint write_scopes (only docs/findings/** shared — new files, disjoint ID ranges); bp-021 asserted at spawn, bp-022 at its own spawn post-bp-021-merge — 2026-07-12, graduation-author's amendments
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/design-notes/code-observation-projection.md # the store being upgraded (§2.2 already states the contract)
  - docs/brainstorms/self-sensing.md # owner capsules: ledger-class ruling, stateless-sensor sharpening
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — B-a: interpreter-version supersession in the observation-store family

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-12 from the **ratified** `dn-self-sensing` (§2.4 mechanism gap, §3.3
B-a, V2's pinned version-identity design, and the owner's 2026-07-12 ledger-class
ruling). Investigation and planning produced this; implementation proceeds item-by-item
on owner approval. `proposed → ready` is the owner's hand edit — no agent flips
readiness. First plan of the family; bp-019 (B-b) and bp-020 (B-c) depend on it.

## 1. Objective

The observation-store family gains an interpreter-version coordinate outside the
identity key — version-keyed projection bookkeeping, archive-then-replace supersession
into a reset-guarded history sidecar, latest-per-identity default reads, the chain
queryable — implemented on the code store (the only member today) in the shape the
agent store (bp-019) inherits.

## 2. Context manifest

1. `docs/design-notes/self-sensing.md` — §2.2 (versioned re-interpretation), §2.4 (the
   mechanism gap + the two orthogonal histories), §2.5 (reset ruling: readings
   corpus-class, history ledger-class), §3.2 V2 (version identity, pinned), §3.3 B-a.
2. `core/stores/code_observations.py` — whole file; the store being migrated.
3. `ops/code_sensor.py` — whole file; the interpreter whose version becomes declared;
   `_project` (`:200-223`) and `backfill_observations` (`:265-278`) are the call sites.
4. `ops/lifecycle/launcher.py:77-78` (`_RESET_GUARD`) and `:496-525` (`reset_targets`)
   — the reset semantics this plan's sidecar joins.
5. `tests/unit/test_code_observations.py`, `tests/unit/test_code_sensor.py` — the
   suites Items 2–4 extend.
6. `docs/design-notes/code-observation-projection.md` §2.2 — the ratified contract
   this plan implements mechanics for (no amendment needed — the note already states
   versioned supersession; only the mechanics were degenerate).

## 3. Investigation & grounding

- **Q1 — what exists today (the degenerate case)?** Identity key
  `PRIMARY KEY (commit_sha, path, qualname)` with `INSERT OR IGNORE`
  (`core/stores/code_observations.py:66,167`); NO interpreter column anywhere in `_DDL`
  (`:54-76`); `projections` bookkeeping keyed by `commit_sha` alone (`:71-75`).
- **Q2 — is the changed-interpreter re-projection today a silent no-op (V2's duty)?**
  YES: `CodeSensor._project` returns `(0, 0)` immediately when
  `self.observations.is_projected(sha)` (`ops/code_sensor.py:207-208`), and
  `is_projected` consults only `commit_sha` (`code_observations.py:200-203`). A changed
  φ_code re-run cannot land rows at all. `mark_projected`'s own comment (`:205-207`)
  promises "re-interpretation is a versioned supersession, §2.2" — the promise this
  plan makes true.
- **Q3 — who calls the store's write/bookkeeping API?** `ops/code_sensor.py` only
  (`_project:200-223`, `backfill_observations:265-278`) plus the two test files. Grep
  confirms no other caller (2026-07-12). The builder re-greps at its HEAD before
  changing signatures.
- **Q4 — does φ_code have ANY version identity today?** No. Nothing in
  `ops/code_sensor.py` or `ops/code_snapshot.py` declares a version; the attestation
  chain records batches (`:221-222`) but no worldview coordinate. Item 1 creates it.
- **Q5 — how does re-projection under a bumped version actually re-run?** `sync()`
  projects only newly-ingested commits (`:160-169`, deliberate per bp-012 §11);
  `backfill_observations()` projects every ledger commit not yet projected (`:265-278`).
  With version-keyed `is_projected`, a version bump makes ALL commits eligible again, so
  **`backfill_observations()` IS the re-projection entry point** — deliberate (run by
  hand or on the owner's nod), never ambient. This matches §2.2's "a deliberate,
  gated workflow-layer act."
- **Q6 — can SQLite alter a PRIMARY KEY additively?** No (`ALTER TABLE` cannot change a
  PK). The `projections` migration is copy-rename (pinned §6(e)); the observations table
  itself keeps its PK and gains only a column — genuinely additive.
- **Q7 — what does the live store hold?** Real rows exist on this machine (the
  post-commit hook has projected every main commit since bp-012 landed). The migration
  must be a healing-on-open (the `backfill_docstrings` precedent,
  `ops/code_sensor.py:171`) so the live file upgrades on first open after merge, with
  no by-hand step.

**Additional risks surfaced during reading:** the `projections` copy-rename migration
must be idempotent (re-open after a crashed migration must heal, not fail); pinned
§6(e) with a marker-column check. Worktree builders share the MAIN checkout's `data/`
only if paths are absolute — they are (`config.loader` anchors to the repo root), so
the builder must run live-file verification against a COPY in its scratch area, never
the main checkout's live store (Item 3 acceptance).

## 4. Reconciliation

- `core/stores/code_observations.py:205-207` — "first mark wins — re-interpretation is
  a versioned supersession, §2.2, not an in-place overwrite" → **[banner: correction]**
  carried by Item 3: the comment described intent, not mechanics; rewritten to describe
  the version-keyed mark that now exists.
- `core/stores/code_observations.py:30-33` (docstring) — "Reset semantics (plan Q4):
  this store is CORPUS-side … unlike the snapshot LEDGER (build history,
  reset-guarded)" → **[cross-ref: extension]** carried by Item 3: still true for
  readings; a sentence is added pointing at the history sidecar as the ledger-class
  half (dn-self-sensing §2.5 ruling).
- `ops/lifecycle/launcher.py:510-513` (the corpus-side comment over
  `code_observations.sqlite`) → **[cross-ref: extension]** carried by Item 4: the
  `_RESET_GUARD` entry's comment names the split (readings wiped, worldview history
  guarded).
- `docs/design-notes/code-observation-projection.md` — **no edit**: the ratified note
  already states the §2.2 contract; `dn-self-sensing` §2.4 records explicitly that "no
  supersession or amendment of the code-observation note is required."

## 5. Write scope

In: the code-observation store, the NEW history-sidecar store, the code sensor, the two
existing test suites plus two new ones, own plan dir, findings. `ops/lifecycle/
launcher.py` is in scope for EXACTLY one `_RESET_GUARD` tuple entry and its comment
(the oq-0013 one-line-grant precedent) — any other launcher change is a stop-and-raise.
Out, deliberately: `core/sensing.py` (bp-019's), design notes, `.githooks/`, the
foundation denylist, `data/**` live stores (verification runs on copies).

## 6. Interfaces pinned inline

**(a) Version identity (V2's pinned design, verbatim from the note):** a declared
semantic version PLUS a content-hash ratchet. In `ops/code_sensor.py`:

```python
INTERPRETER_VERSION = "1.0.0"   # φ_code's worldview coordinate (dn-self-sensing §2.4).
# Bump ⇒ re-projection supersedes (run backfill_observations()); an unbumped source
# change is a RED ratchet test (tests/unit/test_interpreter_versions.py), never silent.
```

`tests/unit/test_interpreter_versions.py` pins, per interpreter, the pair
`(declared version, sha256 of the interpreter's source files)`:

```python
# The ratchet (argless-mypy==69 pattern): change the interpreter source and the test
# reds until you EITHER bump the version and add the new pair (a worldview change —
# re-projection will supersede) OR re-pin the hash at the same version (a declared
# refactor — no worldview change, no re-projection). Both are reviewed, deliberate acts.
INTERPRETERS = {
    "phi_code": Interp(version_attr=("ops.code_sensor", "INTERPRETER_VERSION"),
                       sources=("ops/code_sensor.py", "ops/code_snapshot.py"),
                       version="1.0.0", sha256="<pinned at build>"),
}
```

Rejected (recorded in the note's V2): bare declared constant (a forgotten bump
reproduces the silent no-op being fixed); pure content-hash (every refactor
re-projects, filling the chain with non-worldview noise).

**(b) The history sidecar** (`core/stores/observation_history.py`, NEW — one store for
the FAMILY, discriminated by member name; ledger-class, reset-guarded):

```sql
CREATE TABLE IF NOT EXISTS observation_history (
    store          TEXT NOT NULL,   -- family member: 'code' | 'agent' (bp-019)
    identity_json  TEXT NOT NULL,   -- canonical JSON of the member's identity key
    interpreter    TEXT NOT NULL,   -- the superseded worldview version
    row_json       TEXT NOT NULL,   -- the superseded row, verbatim
    superseded_by  TEXT NOT NULL,   -- the interpreter version that replaced it
    archived_at    TEXT NOT NULL,
    PRIMARY KEY (store, identity_json, interpreter)
);
```

```python
@dataclass
class ObservationHistoryStore:
    path: Path
    def archive(self, store: str, rows: Iterable[tuple[dict, str, str]]) -> int: ...
        # (identity-keyed row, its interpreter, superseding interpreter) → INSERT OR
        # IGNORE. APPEND-ONLY: no delete/update method exists on this class — ledger-
        # class is structural, like the no-provenance-parameter move.
    def chain(self, store: str, identity: dict) -> list[dict]: ...
        # archived generations at one identity key, oldest first
    def count(self, store: str | None = None) -> int: ...

def open_observation_history_store(config=None) -> ObservationHistoryStore: ...
    # data/observation_history.sqlite — GUARDED (Item 4): in _RESET_GUARD, never a
    # reset target. dn-self-sensing §2.5: history does not rebuild (the old
    # interpreters no longer exist at HEAD).
```

**(c) Store write API — new signatures** (`core/stores/code_observations.py`; the only
callers are `ops/code_sensor.py` + tests, Q3):

```python
def add_batch(self, observations: Iterable[CodeObservation], *,
              interpreter: str,
              history: ObservationHistoryStore | None = None) -> tuple[int, int]:
    # returns (new rows, superseded rows). Same identity key + SAME interpreter →
    # INSERT OR IGNORE no-op (idempotence unchanged). Same key + DIFFERENT interpreter
    # → archive the existing row to `history` (store='code'), then replace. history=None
    # with a superseding write is an ERROR (never silently drop a generation).

def is_projected(self, commit_sha: str, interpreter: str) -> bool: ...
def mark_projected(self, commit_sha: str, content_hash: str, interpreter: str) -> None: ...
def chain_for(self, commit_sha: str, path: str, qualname: str,
              history: ObservationHistoryStore) -> list[dict]: ...
    # archived generations + the current row, oldest→current (the queryable chain, §2.4)
```

Default reads (`all_rows`, `rows_for`) are UNCHANGED in signature and semantics: the
main table holds exactly latest-per-identity by construction, so they ARE the
latest-per-identity reads the note requires.

**(d) Observations table migration (additive):** `ALTER TABLE code_observations ADD
COLUMN interpreter TEXT NOT NULL DEFAULT '1.0.0'` on open when absent. Backfilling
existing rows to `'1.0.0'` is honest: they were produced by the current, unchanged
φ_code source — the same worldview Item 1 declares as 1.0.0.

**(e) Projections table migration (copy-rename, idempotent):** on open, if
`projections` lacks the `interpreter` column: create `projections_v2 (commit_sha,
interpreter, batch_hash, projected_at, PRIMARY KEY (commit_sha, interpreter))`, copy
rows with `interpreter='1.0.0'`, drop old, rename. Wrapped in one transaction; re-open
after a crash re-checks the column and heals (the `backfill_docstrings` on-open healing
precedent, `ops/code_sensor.py:171`).

**(f) The reset-guard line** (`ops/lifecycle/launcher.py:77-78` — Item 4's one entry):

```python
_RESET_GUARD = ("vault", "runs.sqlite", "selfmod_ledger.sqlite", "telemetry.duckdb",
                "code_snapshots.sqlite", "observation_history.sqlite",  # ← the addition
                "backup-staging", "logs")
```

**(g) Attestation — unchanged shape:** `project_observations` keeps
`input_hashes=[sha]`, `output_hashes=[batch content hash]` (`ops/code_sensor.py:221-222`).
The version travels in the store, not the chain (the chain's hash already covers the
batch content; adding the version to the action name would fork the vocabulary — P3-
class stability, same reasoning as bp-016's preserved action names).

## 7. Items

_(new family; numbering continues into bp-019/bp-020)_

### Item 1 — φ_code's declared version + the ratchet test

- **Objective:** `INTERPRETER_VERSION = "1.0.0"` in `ops/code_sensor.py` per §6(a);
  `tests/unit/test_interpreter_versions.py` pins (version, source-hash) with the
  bump-or-re-pin discipline in its docstring.
- **Files:** `ops/code_sensor.py`, `tests/unit/test_interpreter_versions.py`
- **Acceptance test:** the new test passes at HEAD; then mutate one byte of
  `ops/code_sensor.py` in the worktree and show the test RED (falsifier-demo), revert.
- **Falsifier:** an interpreter-source edit that leaves the suite green without a
  version bump or an explicit re-pin — the ratchet is toothless.
- **Invariant(s):** no behavior change to sync/projection in this item.
- **Touches stored data?** no
- **Parallelizable?** yes (with Item 2) **Depends on:** none

### Item 2 — the history sidecar store (ledger-class, append-only)

- **Objective:** `core/stores/observation_history.py` per §6(b) +
  `tests/unit/test_observation_history.py`.
- **Files:** `core/stores/observation_history.py`, `tests/unit/test_observation_history.py`
- **Acceptance test:** archive → chain round-trip; INSERT OR IGNORE idempotence;
  `count`; a grep-level assertion in the test that the class defines no
  delete/update method (append-only pinned structurally).
- **Falsifier:** any API path that removes or mutates an archived row (ledger-class
  violated), or a second identical `archive` call changing `count`.
- **Invariant(s):** append-only; no provenance parameter anywhere (rows are archived
  verbatim — provenance already inside `row_json`).
- **Touches stored data?** no (new store; tests use tmp paths)
- **Parallelizable?** yes (with Item 1) **Depends on:** none

### Item 3 — store migration: interpreter column, version-keyed bookkeeping, archive-then-replace

- **Objective:** `code_observations.py` per §6(c,d,e); docstring/comment
  reconciliations (§4).
- **Files:** `core/stores/code_observations.py`, `tests/unit/test_code_observations.py`
- **Acceptance test:** suite green, including NEW tests: (i) same-version re-add is a
  no-op; (ii) bumped-version add archives old + replaces + `chain_for` returns both
  generations ordered; (iii) superseding write with `history=None` raises; (iv) both
  migrations heal on a pre-B-a fixture file AND on a re-opened half-migrated file;
  (v) a COPY of the live `data/code_observations.sqlite` (made into the builder's
  scratch area) opens, migrates, and preserves row count exactly.
- **Falsifier:** the note's B-a falsifier — a re-projection under a bumped interpreter
  version either mutates rows in place (no archived generation) or is silently ignored
  (old bookkeeping shadows the new version).
- **Invariant(s):** provenance stays structural (no parameter appears anywhere);
  identity key unchanged; default reads unchanged; same-interpreter idempotence
  unchanged.
- **Touches stored data?** yes — via the on-open migration after merge. Dry-run
  discipline: acceptance (v) proves the migration on a live-file COPY before any merge;
  the live store migrates itself on the first post-merge sync.
- **Parallelizable?** no **Depends on:** Items 1, 2

### Item 4 — sensor plumbing + the reset guard entry

- **Objective:** `CodeSensor._project`/`backfill_observations` pass
  `INTERPRETER_VERSION` through `is_projected`/`add_batch`/`mark_projected`; the sensor
  gains the history-store handle (wired in `build_code_sensor`); `_RESET_GUARD` gains
  `observation_history.sqlite` per §6(f).
- **Files:** `ops/code_sensor.py`, `ops/lifecycle/launcher.py`,
  `tests/unit/test_code_sensor.py`
- **Acceptance test:** suite green incl. NEW test: project a fixture commit at v1, bump
  the version constant (monkeypatch), run `backfill_observations()` → the commit
  re-projects, old rows archived, `projected` counts it; `reset_targets()` still lists
  `code_observations.sqlite` and REFUSES `observation_history.sqlite` (the existing
  guard assertion `launcher.py:523` covers it — test pins it).
- **Falsifier:** after a version bump, `backfill_observations()` re-projects zero
  commits (the version key is not live end-to-end); or reset would wipe the sidecar.
- **Invariant(s):** `sync()` still projects only newly-ingested commits (re-projection
  stays deliberate, Q5); attestation shape unchanged (§6(g)); launcher change is the
  one tuple entry only.
- **Touches stored data?** no (tests on fixtures; live effect is Item 3's migration)
- **Parallelizable?** no **Depends on:** Item 3

## 8. Math carried explicitly

N/A — no mathematical object implemented (an identity-key/version-coordinate split and
append-only bookkeeping; the content hash is the existing `batch_content_hash`).

## 9. Non-goals

The agent store and φ_self (bp-019); any backfill run (bp-020); wiring
`backfill_observations()` into `sync()` (stays deliberate — bp-012 §11's parked
decision unchanged); attestation vocabulary changes; any launcher change beyond the one
guard entry; consumers of chains (none are licensed).

## 10. Stop-and-raise conditions

Any caller of the store's write API beyond `ops/code_sensor.py` + tests surfaces at
build time (Q3 re-grep) — stop, the signature change has unmapped blast radius; the
live-copy migration in Item 3(v) loses or alters any row — stop, the migration design
is wrong; the launcher needs more than the one tuple entry — stop, file a finding
(scope was mis-granted); any need to touch `core/sensing.py` (that is bp-019's seam —
spec-defect finding if B-a genuinely needs it).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
| --- | --- | --- | --- |
| history mechanism | separate guarded sidecar file, family-shared, archive-then-replace (dn-self-sensing §2.5 pinned at graduation, here) | single-file in-table superseded rows + whole-store reset guard (current readings would survive reset — contradicts corpus-class wipe); single-file + store stays reset target (history dies with every reset — contradicts the ledger-class ruling); selective in-file reset deletion (reset logic grows beyond the one-line launcher precedent) | a built consumer needs single-file chain reads AND measures the two-store join as its dominant cost |
| history grain | whole superseded row archived verbatim (`row_json`) | diff-only storage (smaller, but reconstruction couples the sidecar to every member's schema history) | sidecar size measurably matters (~months of chains) |
| version placement in attestation | store-only; chain action names unchanged (§6(g)) | action-name suffix (forks the chain vocabulary — P3-class instability) | a chain consumer needs worldview lookup without opening the store |
| pre-B-a rows' interpreter | backfilled `'1.0.0'` (honest — same unchanged source) | sentinel `'0.0.0'` / `'unversioned'` (creates a fake worldview generation no interpreter ever declared) | never — decided here |

## 12. Dependency & ordering summary

{Item 1 ∥ Item 2} → Item 3 → Item 4. All reversible code/test writes except Item 3's
on-open migration (proven on fixtures + a live-file copy first). Cross-plan: **bp-019
depends on this plan** (the agent store inherits §6(b,c) mechanics); **bp-020 depends
on bp-019**. Parallelizable with nothing in-family; the owner may run it alongside
unrelated plans (disjoint scope) at their discretion.

---
type: build-plan
id: bp-031
status: proposed
design_ref:
  - docs/design-notes/temporal-retrieval-algebra.md
contract: builder
write_scope:
  - core/stores/catalog.py
  - core/ingest/sync.py
  - core/stores/versions.py
  - tests/integration/test_rename_identity.py
  - tests/integration/test_version_history.py
  - tests/integration/test_vault_sync.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-14
updated: 2026-07-14
links:
  - docs/design-notes/temporal-retrieval-algebra.md
  - docs/design-notes/supersession-lifecycle.md
  - docs/inbox/owner-questions.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — rename-stable document identity (the A6 hard prerequisite)

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan (grounded pass against the identity stores, citations
inline §3); implementation proceeds **item-by-item on owner approval**. This is the **FIRST graduated
plan** of `dn-temporal-retrieval-algebra` — the A6 ruling (note §2.4 / Owner rulings 2026-07-14):
*rename-stable identity is a HARD PREREQUISITE, not an optimization; it gates the diachronic reader,
Result-1 hypothesis H1, and β\*-over-lineage.* Authority-to-act (the owner's instruction to build) is
separate from the readiness blessing (owner-only `proposed → ready`, by hand); no agent flips readiness.

**One design decision is deliberately UNRESOLVED and owner-gated** — the identity *mechanism* (§11,
routed as **oq-0019**). The note left it open on purpose ("front-matter uuid **or equivalent**",
`supersession-lifecycle.md:290`); inferring it to make the plan look finished is the A4 defect. So the
plan is split at the mechanism seam: **Item 1 is mechanism-agnostic and buildable on blessing**; Items
2–3 park on the owner's mechanism ruling and proceed after (never-block).

**Touches live stores (opus/high, scrutinized).** The catalog and version stores are live corpus
bookkeeping. The whole de-risking strategy is **behavior-preservation**: `doc_id` is introduced equal
to `source_path` for every existing row, so today's behavior is byte-identical and the ~20 tests that
key on `source_path` stay green (§3 Q5). A reddening of any *other* existing test is the signal that
Item 1 was not additive — a stop-and-raise (§10), never a scope-widen.

## 1. Objective

Introduce a stable `doc_id` decoupled from `source_path` so a file **rename** no longer forks the
version-history lineage — the note's history stays one chain under one identity.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/temporal-retrieval-algebra.md` — §2.4 (A6, the four well-foundedness conditions),
   Owner rulings (the A6 prerequisite), Parked TA — the *why* and the exact prerequisite this closes.
2. `core/ingest/sync.py` — `VaultSync.sync_path` / `handle_deleted` / `rescan`: the ingest engine that
   keys everything on `source_path` and is where rename detection + `doc_id` resolution mount.
3. `core/stores/catalog.py` — `VaultCatalog` (`vault_files` PRIMARY KEY `source_path`): the store that
   lacks a stable-id notion and gains `doc_id`.
4. `core/stores/versions.py` — `VersionStore` (already keyed on a generic `doc_id` column): the store
   whose **schema is unchanged** — only the *value* sync passes as `doc_id` changes.
5. `core/ingest/logseq.py` — `parse_note` / `parse_text` (`_PROP` regex): confirms `id::`-style
   properties are ALREADY parsed into `ParsedNote.properties` (no new parsing needed to read an
   existing page id; the *minting* question is the parked mechanism).
6. `docs/design-notes/supersession-lifecycle.md` §7 — the "Rename stability" parked constraint this
   plan is the re-entry for (ratified/immutable — cross-referenced, never edited).
7. `tests/integration/test_version_history.py`, `tests/integration/test_vault_sync.py` — the two
   store/sync test homes most likely to touch the visible identity surface.

## 3. Investigation & grounding

- **Q1 — Where exactly does identity fork on rename?** In `sync.py`: `parse_note` sets
  `source_path = str(path)` (`logseq.py:71`), and every store call keys on it —
  `catalog.get(source_path)` (`sync.py:89`), `catalog.record(source_path, …)` (`:99`), and crucially
  `version_store.record(source_path, digest)` (`:112`). A rename presents as delete-old + add-new in
  `rescan` (`:123-134`): `handle_deleted(old_source_path)` tombstones the old row (`:115-121`) and
  `sync_path(new_path)` opens a **fresh version chain at seq 1** under the new `source_path`. The old
  chain is orphaned — *version continuity lost* (`supersession-lifecycle.md:287-289`). **The code settles
  this.**
- **Q2 — Does the version store need a schema change?** **No.** `versions.py:54,59` already defines
  `doc_id TEXT` as the identity column (PRIMARY KEY `(doc_id, version_seq)`), documented as "stable
  document identity (the catalog source_path)". Today `sync.py:112` merely passes `source_path` *as*
  that `doc_id`. Resolving a stable `doc_id` and passing THAT leaves the versions schema untouched. **The
  code settles this** — this is the single biggest de-risking fact.
- **Q3 — Does the catalog carry a stable id today?** No. `vault_files` PRIMARY KEY is `source_path`
  (`catalog.py:33`); there is no `doc_id` column. **The catalog is the store that must gain the
  `source_path → doc_id` mapping. The code settles this.**
- **Q4 — Is a stable id already available without new parsing or vault mutation?** *Partially.*
  `parse_note` already extracts `id::`-style properties into `ParsedNote.properties` via `_PROP`
  (`logseq.py:19,64,71`) — so an **existing** Logseq page id is readable with zero new code and zero
  vault mutation. But **not every note has one**, and **the code does NOT settle what to do when it is
  absent**: mint one and write it back to the vault (mutates the owner's corpus), detect renames by
  content lineage on rescan (heuristic, exact only for rename-without-edit), or an external-only id map
  (same detection problem). *What would settle it: an owner ruling on the mechanism* — **oq-0019 / §11.**
- **Q5 — What is the blast radius of adding `doc_id` to the catalog?** Wide by reference but narrow by
  *behavior*: `source_path`/`VaultCatalog`/`VersionStore` are referenced across ~20 test files (grep,
  2026-07-14). **Behavior-preservation contains it**: backfill `doc_id := source_path` for every existing
  row and default resolution to `source_path` when no id is present ⇒ every current `source_path`-keyed
  path and assertion is byte-identical. **The code does not settle whether an additive column vs a
  side `doc_identity(doc_id, source_path)` table is cleaner** — Item 1 chooses the least-migration form;
  either is behavior-preserving.

**Additional risks or questions surfaced during reading:** (a) `rescan` sees delete+add together
(`:129-134`) so content-lineage rename detection is *possible* there, but the incremental watcher path
(`core/ingest/watch.py`, not in scope) may see them as separate events — the mechanism ruling must state
whether rename-stability is guaranteed only on full rescan or also incrementally. (b) A no-op re-save
must stay an *occurrence*, not a phantom version (`supersession-lifecycle.md:292-294`) — the existing
`UNCHANGED` short-circuit (`sync.py:90-91`) already guarantees this and must not regress.

## 4. Reconciliation

- `docs/design-notes/supersession-lifecycle.md §7` — *"Parked: adopt a rename-stable identity
  (front-matter uuid or equivalent) before large corpus reorganization; re-entry condition recorded."*
  → **[cross-ref: extension]** This plan **is** that re-entry: `dn-temporal-retrieval-algebra`'s A6
  ruling promoted the parked constraint to a hard prerequisite. Both notes are **ratified/immutable** —
  this plan **cross-references, never edits** either. No banner is applied to a ratified note by an agent.
- `core/stores/versions.py:55` — the inline comment *"stable document identity (the catalog
  source_path)"* becomes **inaccurate** once `doc_id ≠ source_path`. → **[banner: correction]** Item 1
  updates the comment (and the module-docstring line 26 "keyed on … the catalog source_path") to state
  `doc_id` is now the stable identity *resolved by sync*, no longer literally the `source_path`. This is
  a comment/docstring correction carried by an item, not a quiet edit — the schema and behavior are
  unchanged.

## 5. Write scope

Front-matter: `core/stores/catalog.py` (add the `doc_id` mapping + resolver), `core/ingest/sync.py`
(resolve `doc_id`; rename carry-forward), `core/stores/versions.py` (**comment/docstring correction
only** — schema unchanged, §4), and three test paths — `tests/integration/test_rename_identity.py`
(NEW, the payoff proof), plus `tests/integration/test_version_history.py` and
`tests/integration/test_vault_sync.py` (the two store/sync homes that may need a visible-surface touch).
**Deliberately OUT of scope:** `core/ingest/logseq.py` (`id::` is already parsed — read
`parsed.properties`, no change); `core/ingest/watch.py` (the incremental path — the mechanism ruling
decides if it is in a later item); **the vault itself** (minting an id INTO a note mutates the owner's
corpus — owner-gated, never done without an explicit grant, §10); the `core/temporal/` module (bp-032);
every design note and the denylist.

## 6. Interfaces pinned inline

```python
# core/stores/catalog.py — TODAY (identity = source_path; the store that gains doc_id):
_DDL = "CREATE TABLE IF NOT EXISTS vault_files (source_path TEXT PRIMARY KEY, digest TEXT NOT NULL, "\
       "title TEXT NOT NULL, provenance TEXT NOT NULL DEFAULT 'authored-solo', "\
       "active INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL); ..."
def get(self, source_path: str) -> CatalogEntry | None: ...
def record(self, source_path: str, digest: str, title: str, *, provenance=...) -> None: ...  # upsert
def tombstone(self, source_path: str) -> str | None: ...      # active=0, returns held digest
def active_paths(self) -> set[str]: ...                       # rescan uses: active_paths() - seen

# core/stores/versions.py — UNCHANGED SCHEMA (already doc_id-keyed; only the passed VALUE changes):
#   versions(doc_id TEXT, version_seq INTEGER, digest TEXT, at TEXT, PRIMARY KEY (doc_id, version_seq))
def record(self, doc_id: str, digest: str) -> Version: ...    # seq = current+1 or 1; append-only
def history(self, doc_id: str) -> list[Version]: ...          # the append-only chain, seq order
def supersessions(self, doc_id: str) -> list[tuple[int, int]]: ...  # consecutive-seq pairs

# core/ingest/sync.py — TODAY (source_path is passed straight through as the version doc_id):
def sync_path(self, path: Path) -> SyncOutcome:
    parsed = parse_note(path, self.vault)          # parsed.properties HAS 'id' if the note has id::
    source_path = parsed.source_path               # == str(path)  (logseq.py:71)
    ...
    self.catalog.record(source_path, digest, record.title)
    if self.version_store is not None:
        self.version_store.record(source_path, digest)   # ← Item 1: pass a resolved doc_id here
def handle_deleted(self, source_path: str) -> SyncOutcome:  # tombstone + drop projection

# core/ingest/logseq.py — the id is ALREADY available (no change needed to READ it):
_PROP = re.compile(r"^([A-Za-z0-9_-]+)::\s?(.*)$", re.MULTILINE)   # captures `id:: <uuid>`
@dataclass(frozen=True)
class ParsedNote:
    source_path: str; title: str; text: str
    tags: frozenset[str]; links: frozenset[str]; properties: dict[str, str]   # properties['id'] if present
```

## 7. Items

### Item 1 — the `doc_id` foundation (additive, behavior-preserving)
- **Objective:** give the catalog a stable `doc_id` (default `doc_id := source_path`, backfilled for
  every existing row) + a `doc_id_for(source_path) -> str` resolver, and route sync's
  `version_store.record(...)` through the resolved `doc_id`. **Today's behavior is byte-identical**
  (doc_id == source_path everywhere until a mechanism diverges it).
- **Files:** `core/stores/catalog.py` (the `doc_id` mapping + resolver + backfill migration),
  `core/ingest/sync.py` (resolve `doc_id`, pass it to `version_store.record`), `core/stores/versions.py`
  (comment/docstring correction, §4).
- **Acceptance test:** on a fresh store, ingest → `catalog.doc_id_for(p) == p` and
  `version_store.history(doc_id_for(p))` matches the pre-change chain exactly; on a store with
  legacy rows, the backfill sets `doc_id = source_path` for all and `test_version_history.py` +
  `test_vault_sync.py` stay green unchanged.
- **Falsifier:** any existing test **other than** the two listed reddens (⇒ the change was not additive —
  §10); OR a legacy `versions` row's chain is renumbered/split by the migration (the backfill must be a
  pure relabel, never a re-key).
- **Invariant(s) it must not violate:** append-only version history (`versions.py` never mutates a prior
  row); the `UNCHANGED` no-op short-circuit (`sync.py:90-91`) — a no-op re-save stays an occurrence, not
  a phantom version; content-addressing of raw/vectors unchanged.
- **Touches stored data?** **Yes** (adds/backfills `doc_id` in the catalog) → a dry-run migration
  verification on a copy of the live catalog precedes any real write; the backfill is idempotent.
- **Parallelizable?** No (shares sync.py with Items 2–3).  **Depends on:** none.

### Item 2 — `doc_id` resolution mechanism + rename carry-forward  ⟨OWNER-GATED — oq-0019⟩
- **Objective:** resolve `doc_id` from an **existing** `id::` property when present (non-mutating,
  `parsed.properties.get("id")`), and carry `doc_id` forward across a rename so the chain does not fork —
  by the mechanism the owner rules (§11 / oq-0019; recommended default: existing-id + exact-content
  rename detection on rescan, **no** mint-into-vault).
- **Files:** `core/ingest/sync.py` (resolution + rename detection in `sync_path`/`rescan`),
  `core/stores/catalog.py` (update the `source_path` bound to a `doc_id` on rename).
- **Acceptance test:** a note carrying `id:: X` keeps `doc_id == X` across a `source_path` change; a
  rescan that sees a tombstone of path A and an add of path B with A's exact last content carries A's
  `doc_id` to B (per the ruled mechanism).
- **Falsifier:** after a pure rename, `version_store.history(doc_id)` shows a fresh seq-1 chain (fork not
  fixed); OR resolution mutates a vault file (a corpus write happened without an owner grant — §10).
- **Invariant(s):** never write to the vault absent an explicit owner grant; a rename+edit (ambiguous)
  falls back to a new lineage — same as today, no worse (§11).
- **Touches stored data?** Yes (rebinds `source_path`↔`doc_id`) → dry-run first.
- **Parallelizable?** No.  **Depends on:** Item 1; **the owner's mechanism ruling (oq-0019).**

### Item 3 — the rename-stability proof
- **Objective:** the falsifiable proof that a rename preserves lineage — the artifact that lets the
  diachronic reader / Result-1 H1 rely on rename-stable identity.
- **Files:** `tests/integration/test_rename_identity.py` (NEW).
- **Acceptance test:** ingest note at path A (versions v1, v2) → rename A→B → rescan → assert
  `version_store.history(doc_id)` is the **single continuous chain v1,v2,v3** under **one** `doc_id`
  (no orphaned seq-1 chain), and `catalog.doc_id_for(B)` equals the pre-rename `doc_id`.
- **Falsifier:** two distinct `doc_id`s exist for the one note's lineage after the rename (the fork the
  A6 ruling exists to kill); OR the test passes only because rename detection silently mutated the vault.
- **Invariant(s):** the test makes **no** network/model call; deterministic.
- **Touches stored data?** No (temp stores).  **Depends on:** Item 2.

## 8. Math carried explicitly

**N/A — no mathematical object implemented.** This is a data-model/identity change (rename-stable
`doc_id`). It is a *prerequisite* for the note's math (Result-1 H1 rename-stability, `δ_D²=0`
well-foundedness, β\*-over-lineage) but implements none of it — that is bp-032 and the diachronic reader.
The A6 "op-seq well-order" is already realized by the existing monotonic `version_seq` (`versions.py`).

## 9. Non-goals

- **No diachronic reader, no `core/temporal/` module** (bp-032 and later).
- **No vault mutation.** Minting an `id::` INTO a note is explicitly deferred to the owner's mechanism
  ruling; this plan reads existing ids only.
- **No change to tombstone/purge semantics, raw-is-sacred, or content-addressing.**
- **No incremental-watcher rename handling** unless the mechanism ruling puts it in Item 2's scope
  (default: rescan-only).

## 10. Stop-and-raise conditions

- **An existing test other than the two in write_scope reddens on Item 1** → the change was not
  behavior-preserving. **File a `codebase` finding, narrow Item 1 back to additive; do NOT self-widen
  write_scope** (finding-0075 discipline: correcting a blessed plan's write_scope is owner-gated).
- **The mechanism decision surfaces** → Items 2–3 are owner-gated; **park them with re-entry (oq-0019)
  and proceed with Item 1** (never block on the owner).
- **Any path would require writing to the vault** (mint-into-vault) → that mutates the owner's corpus →
  **STOP and surface**; do not write a vault file without an explicit owner grant.
- Any blessing flip → must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| **The identity mechanism** (the load-bearing one — **oq-0019**) | Prefer an **existing** `id::` property when present (non-mutating, already parsed); else **exact-content rename detection on rescan** (deterministic); **do NOT mint-into-vault by default** | *Mint-into-vault* (write `id::` into every note): guarantees stability but **mutates the owner's authored corpus** — owner-gated, blast-radius on the vault. *Pure content-heuristic only:* ambiguous on rename+edit (content changed) — can't distinguish rename from new note. *External-only id map, no rescan detection:* has the same rename-detection gap, adds a store for no coverage gain | **Owner rules at `proposed → ready` / oq-0019.** Items 2–3 build on the ruled mechanism |
| Rename **+ edit** (content also changed) ambiguity | New lineage (same as today — no regression) | Fuzzy content-similarity match (rejected v1: non-deterministic, needs a threshold with no falsifier) | a measured rename+edit frequency warrants fuzzy matching, or the owner rules mint-into-vault (which makes it exact) |
| Incremental-watcher rename-stability | Rescan-only in v1 | Cover the incremental path too (deferred: the watcher sees delete/add as separate events — needs a debounce/pairing design) | the mechanism ruling extends Item 2 to `watch.py` |

## 12. Dependency & ordering summary

Blast-radius order (all within one session): **Item 1** (additive, behavior-preserving foundation —
buildable immediately on blessing) → **Item 2** (mechanism-dependent resolution + rename carry-forward —
**owner-gated on oq-0019**, parks without blocking Item 1) → **Item 3** (the rename-stability proof test,
depends on Item 2). All three share `sync.py` → one session, not parallel. Model: **opus** (live-store
migration + a behavior-preservation falsifier that needs judgment). `depends_on: []` (this is the FIRST
plan); **bp-032 (`core/temporal/`) and the diachronic reader `depends_on: bp-031`** — the A6 hard
prerequisite: their `δ_D`/version chains and β\*-over-lineage require rename-stable `doc_id`.

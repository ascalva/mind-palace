---
type: build-plan
id: bp-034
status: complete
design_ref:
  - docs/design-notes/temporal-retrieval-algebra.md   # A6 rename-stable identity; oq-0019 ruled (B)
contract: builder
write_scope:
  - core/ingest/mint_ids.py
  - scripts/mint_ids.py
  - core/stores/versions.py
  - core/stores/catalog.py
  - tests/integration/test_mint_ids.py
  - tests/unit/test_version_rekey.py
  - core/stores/authored_supersession.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 450k
  actual:
    model: opus            # self-driven, high effort, single-lane (0 subagents; 3 Explore scouts)
    tokens: 175k           # non-cache: 38.9k in + 136.0k out (+ 26.3m cache read). Owner /usage.
    dollars: 20.36         # full session (started at 0%; the whole session WAS bp-034)
    ratio: 0.39            # 175k / 450k — within the self-driven single-lane band (est 0.5–0.8x)
    session_delta: "+13pp (0%->13%)"      # the 5-hour session window
    week_delta: "+1pp (81%->82%, cache-dominated — light on the weekly quota)"
    # Credits UNCHANGED at 89% ($89.59/$100, resets Aug 1) — this session was covered by the
    # weekly/subscription allowance, not billed to credits. Start-of-session week was 81%.
depends_on:
  - bp-031
parallelizable_with: []
created: 2026-07-14
updated: 2026-07-14   # SEALED — Items 13-16 built + green (1078 passed); tool delivered, mint owner-run
links:
  - docs/design-notes/temporal-retrieval-algebra.md
  - docs/design-notes/supersession-lifecycle.md
  - docs/inbox/owner-questions.md          # oq-0019 (B ruling)
  - docs/findings/finding-0066.md          # live-daemon store migration is deploy-coupled
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/inbox/owner-questions.md    # oq-0019 ruled (B); this plan is that ruling's follow-on
---

# Build Plan — the id-mint migration: durable `id::` identity + version re-key (oq-0019 B)

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan (grounded pass against the ingest + store code, citations
inline §3); implementation proceeds **item-by-item on owner approval**. It is the **follow-on to
oq-0019's (B) ruling** (owner, 2026-07-14): adopt a minted Logseq `id::` as the durable, rename-stable
document identity — the exact-in-all-cases mechanism (A/C fork on rename+edit; B does not). `depends_on:
bp-031` (which decouples `doc_id` from `source_path` and resolves `doc_id` from an existing `id::`).

**This plan BUILDS THE TOOL; it does NOT run the migration.** Mirroring `core/ingest/purge.py` /
`scripts/purge_raw.py` — the repo's existing owner-gated, irreversible-data operation — the mint is a
**deliberate, owner-run, offline act**, never fired in a build session and never by the watcher. The
build delivers a dry-runnable, `confirm`-gated, idempotent, reversible migrator + its owner-facing
script + tests; the **owner runs it once, corpus-wide, with the daemon DOWN** (a live-store migration is
DEPLOY-COUPLED — finding-0066).

**Highest-blast plan authored to date (opus/high, maximal scrutiny).** It is the FIRST operation that
**writes the owner's authored corpus** (the vault) and the FIRST that **relabels the append-only version
store**. Two invariant-adjacent facts are surfaced for the owner, not decided by the plan: (i) the vault
write crosses "the mirror never writes the corpus" — accepted as an owner-gated act by oq-0019; (ii) the
version-store re-key touches its structural **append-only "no update/delete"** contract (§4, §10, §11).

## 1. Objective

Deliver an owner-gated, offline, idempotent, reversible migrator that mints a durable `id::` into each
vault note lacking a stable id **and** re-keys that note's version history from `source_path` to the
minted id — so no lineage forks at the identity switch, now or on any future rename.

## 2. Context manifest

Read whole, in order:

1. `docs/inbox/owner-questions.md` — **oq-0019** (the B ruling, its rationale, and the re-key as the
   load-bearing step this plan implements).
2. `docs/design-notes/temporal-retrieval-algebra.md` §2.4 — A6 (rename-stable identity; the four
   well-foundedness conditions this migration finally satisfies).
3. `core/ingest/purge.py` + `scripts/purge_raw.py` — **the pattern to mirror**: an owner-gated
   (`confirm=True`, fail-closed) irreversible-data operation with a safety-refusal gate; NOT the
   watcher's default; an owner-facing script entry.
4. `core/ingest/sync.py` — `VaultSync.sync_path`/`rescan`; where `doc_id` is resolved (post-bp-031) and
   where the re-ingest of a minted note lands as an amendment.
5. `core/stores/versions.py` — the append-only version store (`doc_id` PK component; the "no
   update/delete" structural invariant; `record`/`history`/`supersessions`). **The re-key target.**
6. `core/stores/catalog.py` — `VaultCatalog` (post-bp-031 `doc_id` column); `relabel_provenance:124`
   (the **owner-era relabel-UPDATE precedent**). **The second re-key target.**
7. `core/ingest/index.py` — `rekey_store`/`rekey_preview` (`:91-112`, the dry-run-previewed idempotent
   migration precedent); `_chunk_row:32` + `index_amendment:80` proving the vector store is
   **`source_path`-keyed and self-heals** (no re-key needed).
8. `core/ingest/logseq.py` — `parse_note`/`_PROP` (`:19`): how `id::` is parsed; the byte-preserving
   insertion point (page-properties in the first block).
9. `core/stores/authored_supersession.py` — **digest**-keyed (not doc_id); confirms it needs NO re-key,
   AND models the owner-authority capability gate (`OwnerDeclaration`) this migrator should adopt.
10. `config/defaults.toml` `[vault]` (`:42-47`) — `path`/`pattern`: the migration's scope surface.

## 3. Investigation & grounding

- **Q1 — What EXACTLY must be re-keyed, and what self-heals?** Grounded, tight surface:
  - **`versions`** — keyed by `doc_id` (`versions.py:59`). `doc_id` changes `source_path → minted id`.
    **MUST re-key explicitly** — the store is append-only (no self-heal): a re-ingest under the new id
    calls `record(new_id, …)` whose `current(new_id)` is `None` → **seq 1 → a forked chain**
    (`versions.py:88-94`). *The code settles this — it is the load-bearing fact.*
  - **`catalog.doc_id`** (post-bp-031 column) — should be re-keyed to the minted id so resolution is
    consistent; **re-key explicitly** (do not rely on an upsert side effect). PK `source_path` is
    unchanged by the in-place mint (`catalog.py:33`).
  - **Vector store** — chunk rows keyed by `(source_path, chunk_hash)` (`index.py:32,88`), NOT doc_id;
    `source_path` is unchanged by an in-place mint, so `index_amendment` re-projects under the same key
    (`index.py:80`) — **self-heals, NO re-key.** *The code settles this.*
  - **Raw store + `authored_supersession`** — **digest**-keyed (`rawstore` content address;
    `authored_supersession.py:98`). The mint changes a note's digest, but the pre-mint digest's raw blob
    is KEPT (raw is sacred) and existing rows reference persistent historical digests → **NO re-key.**
    *The code settles this.*
- **Q2 — Does the mint edit itself fork lineage? (the owner's question.)** No — *if and only if the
  re-key precedes/accompanies the re-ingest.* The mint is an **in-place** edit (path unchanged), so
  `catalog.get(source_path)` still finds the row and `digest != prev.digest` → `INDEXED` → a normal
  amendment (`sync.py:89-113`). But the amendment `record`s under the RESOLVED doc_id (the minted id),
  so **without the Q1 re-key it appends a fresh seq-1 chain.** The re-key is what carries the pre-mint
  history onto the new id. *The code settles this; it is precisely why the digest-change alone is
  insufficient (oq-0019).*
- **Q3 — Does re-keying `versions` violate its append-only invariant?** `versions.py` is structurally
  "append + reads only (no update/delete)" — a relabel UPDATE touches that. **The code does NOT settle
  whether an owner-gated re-key is admissible; that is an owner ruling.** Two facts frame it: (i) the
  re-key preserves every row's `(version_seq, digest, at)` exactly — it **relabels identity, does not
  rewrite history** (the sequence, contents, and order are invariant); (ii) `catalog.relabel_provenance`
  (`catalog.py:124`) is an existing **owner-era relabel-UPDATE migration** precedent. *What would settle
  it: an owner ruling that the append-only store admits an owner-authorized `migrate_rekey_doc_id`
  (relabel), distinct from the runtime `record` path* — surfaced §10/§11.
- **Q4 — Which notes get minted, and is it idempotent?** Only vault notes (`cfg.vault.path`/`pattern`,
  `defaults.toml:42-47`) that **lack a stable id** — no Logseq `id::` (`parsed.properties.get("id")`)
  AND no YAML `id:` front-matter. **Idempotent-skip** any note already carrying a stable id (a second
  run mints nothing). *The code settles the detection* (`logseq.py:19` parses both `key:: value` and, if
  present, YAML — verify the YAML case during build). **This handles the "design notes / docs" concern
  (owner's phrasing):** repo design-notes/findings already carry YAML `id:` (`id: dn-…`/`finding-…`) and
  are skipped even if the vault points at them.
- **Q5 — What are the side effects of the mint, and are they acceptable?** (a) Each minted note's bytes
  change → **one new version per note** ("id added" amendment) — a one-time, corpus-wide, logged version
  bump (acceptable; it IS a real change). (b) The `id::` line enters the note's chunked/embedded text —
  but properties already do (any tagged note), so this is consistent, not new pollution. (c) A minted
  note re-embeds only its first (changed) chunk (`index_amendment:74`). *The code settles the mechanism;
  acceptability is recorded here.*

**Additional risks or questions surfaced during reading:** (a) **Watcher/daemon races** — a corpus-wide
vault write would trigger `VaultWatcher` (`core/ingest/watch.py`) and the scheduler's `vault_sync`. The
migration MUST run with the **daemon DOWN** (`palace down`, KeepAlive-aware — bp-030 Item 1) so the
re-key and the re-ingest are serialized under the migrator's control, then verify, then bring it up
(deploy-coupled, finding-0066). (b) **Logseq `id::` format** — page-level properties live in the FIRST
block; the insertion must be byte-preserving except for the added line, and must not disturb an existing
properties block. Confirm the exact Logseq page-property convention during build against a real vault
sample; if it is ambiguous, STOP and raise (§10) rather than guess a format that could corrupt notes.
(c) **uuid source** — mint `uuid4` (Logseq's own convention); the id must be recorded in the note AND be
the value bp-031 resolution reads back (`properties['id']`).

## 4. Reconciliation

- `core/stores/versions.py` module docstring — *"append-only; ... append + reads only (no
  update/delete)."* → **[banner: correction/extension — OWNER-GATED]** this plan adds a
  `migrate_rekey_doc_id(old_doc_id, new_doc_id, *, declaration)` method that RELABELS `doc_id` on
  existing rows (preserving `(version_seq, digest, at)`). It is **not** a runtime write and **not** a
  history rewrite; it is an owner-authorized identity migration, gated by the same `OwnerDeclaration`
  capability `authored_supersession.py` uses. The docstring/invariant note is updated to record the
  admitted migration path explicitly (never a silent broadening). **The owner rules admissibility at
  blessing (§10/§11); if declined, this plan cannot proceed and re-graduates.**
- `oq-0019` (B ruling) names "the version/catalog re-key … `UPDATE … SET doc_id = <minted id> WHERE
  doc_id = source_path`" as the load-bearing step → **[cross-ref]** this plan implements exactly that,
  encapsulated as a store method (not raw SQL in the migrator) for testability + boundary-guarding.
- No design note is edited (both temporal + supersession notes are ratified/immutable — cited only).

## 5. Write scope

Front-matter: `core/ingest/mint_ids.py` (the migrator: detect → dry-run → mint → re-key → verify),
`scripts/mint_ids.py` (the owner-facing entry, mirrors `scripts/purge_raw.py`), `core/stores/versions.py`
(+ the owner-gated `migrate_rekey_doc_id`), `core/stores/catalog.py` (+ `migrate_rekey_doc_id` for the
`doc_id` column), and two test paths — `tests/integration/test_mint_ids.py` (end-to-end offline
migration) + `tests/unit/test_version_rekey.py` (the re-key primitive). **Deliberately OUT of scope:**
`core/ingest/sync.py` (bp-031 owns the resolution; this plan only READS it), the vector/raw stores
(they self-heal / are digest-safe — never touched), `core/ingest/watch.py` + the scheduler (the
migration runs with them DOWN, not modified), every design note, the denylist, **and the vault contents
at build time** (the migrator writes the vault only when the OWNER runs it — the build writes NO vault
file). The mint is not wired into `sync`/the watcher/the scheduler.

## 6. Interfaces pinned inline

```python
# core/stores/versions.py — TODAY (append-only; the re-key target):
#   versions(doc_id TEXT, version_seq INTEGER, digest TEXT, at TEXT, PRIMARY KEY (doc_id, version_seq))
def record(self, doc_id: str, digest: str) -> Version: ...        # current(doc_id) is None → seq 1 (the fork)
def history(self, doc_id: str) -> list[Version]: ...
def current(self, doc_id: str) -> Version | None: ...
# NEW (this plan) — owner-gated relabel, preserving (version_seq, digest, at):
#   def migrate_rekey_doc_id(self, old: str, new: str, *, declaration: OwnerDeclaration) -> int
#       # UPDATE versions SET doc_id = ? WHERE doc_id = ?  (idempotent if old == new or no rows)
#       # refuses without a valid OwnerDeclaration (authored_supersession.py capability gate)

# core/stores/catalog.py — precedent + NEW:
def relabel_provenance(self, old: str, new: str) -> int: ...      # PRECEDENT: an owner-era relabel UPDATE
def doc_id_for(self, source_path: str) -> str: ...                # bp-031 (post) — the current doc_id
#   def migrate_rekey_doc_id(self, source_path: str, new_doc_id: str, *, declaration) -> None  # NEW

# core/ingest/logseq.py — detection + insertion point:
_PROP = re.compile(r"^([A-Za-z0-9_-]+)::\s?(.*)$", re.MULTILINE)  # parses `id:: <uuid>` into properties['id']
#   ParsedNote.properties['id']  → the stable id if present (skip-if-present, idempotent)

# core/ingest/index.py — PROOF the vector store self-heals (no re-key), + the migration PATTERN:
def _chunk_row(...): return {"id": chunk_point_id(record.source_path, chunk), "source_path": ..., ...}
def rekey_preview(store) -> tuple[int, int]: ...   # dry-run shape to mirror (reads, mutates nothing)

# core/ingest/purge.py — THE OWNER-GATED-OPERATION PATTERN to mirror:
class PurgeRefusedError(RuntimeError): ...
def purge_raw(digest, *, raw, store, catalog, confirm: bool = False) -> PurgeResult:
    if not confirm: raise PurgeRefusedError(...)   # fail-closed: explicit confirm required
    ...                                            # refuses on unsafe precondition

# core/stores/authored_supersession.py — THE OWNER-AUTHORITY CAPABILITY to adopt for the re-key:
def owner_declaration() -> OwnerDeclaration: ...   # construction-guarded; a machine path cannot forge one
```

## 7. Items

### Item 13 — dry-run preview (read-only; mutates NOTHING)
- **Objective:** enumerate, without any write, (a) the vault notes lacking a stable id (the mint set),
  and (b) the `doc_id` re-key plan (`source_path → to-be-minted-id`, or `→ existing id` for notes that
  already carry one) — the migration's auditable plan, printed for the owner before any mutation.
- **Files:** `core/ingest/mint_ids.py` (the `preview()` function), `scripts/mint_ids.py` (`--dry-run`).
- **Acceptance test:** on a fixture vault (some notes with `id::`, some with YAML `id:`, some with none),
  `preview()` lists exactly the no-stable-id notes as the mint set and skips the rest; it opens no write
  handle and modifies no store/file (assert store counts + file mtimes unchanged).
- **Falsifier:** `preview()` mints, writes, or re-keys anything (it must be pure-read); OR it lists a
  note that already has a stable id (idempotency broken at the planning stage).
- **Invariant(s):** read-only; deterministic; no daemon interaction.
- **Touches stored data?** No.  **Parallelizable?** No.  **Depends on:** bp-031.

### Item 14 — the owner-gated version/catalog re-key primitive
- **Objective:** `migrate_rekey_doc_id` on `VersionStore` (and the catalog) — relabel `doc_id`
  `source_path → minted id`, preserving every row's `(version_seq, digest, at)`; `OwnerDeclaration`-gated
  (fail-closed); idempotent (`old == new` or no rows → no-op).
- **Files:** `core/stores/versions.py`, `core/stores/catalog.py`, `tests/unit/test_version_rekey.py`.
- **Acceptance test:** seed a chain `(P, v1..v3)`; `migrate_rekey_doc_id(P, X, declaration=...)` →
  `history(X)` is `v1..v3` byte-identical (same seqs/digests/times) and `history(P)` is empty; a call
  without a valid `OwnerDeclaration` raises (`MachineAuthorityRefused`-style); re-running with `(P, X)`
  again is a no-op.
- **Falsifier:** the re-key changes any `version_seq`/`digest`/`at` (that would be a history rewrite, not
  a relabel — forbidden); OR it succeeds without owner authority; OR `X` already had a chain and the two
  are silently merged/renumbered (must refuse or be explicitly defined — a **stop-and-raise**, §10).
- **Invariant(s):** relabel-not-rewrite (row contents invariant); append-only history integrity
  preserved in substance; owner-authority fail-closed (the `authored_supersession` capability model).
- **Touches stored data?** **Yes** (relabels live version/catalog rows) → a backup of both SQLite stores
  precedes any real run; dry-run (Item 13) previews the exact remap first.
- **Parallelizable?** No.  **Depends on:** bp-031; Item 13.

### Item 15 — the byte-preserving vault minter
- **Objective:** for each mint-set note (Item 13), insert `id:: <uuid4>` into its Logseq page properties
  — **byte-preserving except the single added line** — and return the `source_path → minted id` map for
  the re-key. Idempotent-skip any note that gained a stable id since the preview.
- **Files:** `core/ingest/mint_ids.py` (the `mint()` function).
- **Acceptance test:** on a fixture vault, `mint()` adds exactly one `id:: <uuid>` line to each no-id
  note in the correct page-properties position, changes nothing else in the file (byte-diff = the one
  line), skips notes already carrying `id::`/YAML `id:`, and returns a map whose ids parse back via
  `parse_note(...).properties['id']`.
- **Falsifier:** a minted file differs from the original by more than the id line (content corruption);
  OR an existing property/first-block structure is disturbed; OR a note with an id is re-minted (a second
  id line) — idempotency broken.
- **Invariant(s):** byte-preserving except the added line; the uuid is `uuid4`; NEVER writes a note that
  already has a stable id; writes ONLY under `cfg.vault.path` (never repo files).
- **Touches stored data?** **Yes — the authored corpus (the vault).** The highest blast: a **vault
  backup precedes any real run**; `confirm=True` required; dry-run first.
- **Parallelizable?** No.  **Depends on:** Item 13.

### Item 16 — the owner-facing orchestration + end-to-end verification
- **Objective:** `scripts/mint_ids.py` (mirror `scripts/purge_raw.py`): the offline, `confirm`-gated,
  reversible run — **backup(vault + stores) → dry-run report → [confirm] → re-key stores (Item 14) →
  mint vault (Item 15) → rescan → VERIFY no lineage forked → report**. Refuses unless the daemon is down.
- **Files:** `scripts/mint_ids.py`, `core/ingest/mint_ids.py` (the `run(confirm=...)` orchestrator),
  `tests/integration/test_mint_ids.py`.
- **Acceptance test (the whole point):** an end-to-end fixture — ingest notes (build version chains) →
  run the migrator → assert (a) every note's history is ONE continuous chain under its minted id, **no
  orphaned `source_path` chain** (`history(source_path)` empty, `history(minted_id)` = the full chain +
  the "id added" amendment); (b) a **rename after migration preserves lineage** (the id survives the
  path change — the A6 goal); (c) a **second run is a no-op** (idempotent); (d) without `confirm=True`
  or with the daemon up, it **refuses** (fail-closed).
- **Falsifier:** any note's lineage forks across the migration (an orphaned source_path chain remains) —
  the migration failed its one job; OR a post-migration rename still forks (the id didn't take); OR the
  run mutates anything when `confirm` is absent.
- **Invariant(s):** offline-only (daemon down — finding-0066); reversible (restore from the backups
  reproduces the pre-migration state exactly); raw is sacred (pre-mint digests retained).
- **Touches stored data?** **Yes — vault + version/catalog stores.** Backups + dry-run + confirm all
  precede the real write.  **Depends on:** Items 13, 14, 15.

## 8. Math carried explicitly

**N/A — no mathematical object implemented.** This is a data/identity migration (mint `id::`, relabel
`doc_id`). It is the operational prerequisite that makes the A6 well-foundedness conditions
(`dn-temporal-retrieval-algebra` §2.4) hold on the real corpus, but implements none of the note's math.

## 9. Non-goals

- **No wiring into `sync`/the watcher/the scheduler** — the mint is a one-time owner-run migration, never
  an ambient behavior. bp-031's resolution (read `id::` when present) is the ongoing runtime path.
- **No re-key of the vector/raw/authored-supersession stores** — they self-heal (source_path-stable) or
  are digest-safe (§3 Q1). Touching them would be a defect.
- **No minting into notes that already carry a stable id** (Logseq `id::` or YAML `id:`) — idempotent
  skip; this is what keeps repo design-notes/findings (already `id:`-stamped) untouched.
- **No running the migration in a build session** — the build ends with a tested, dry-runnable tool; the
  OWNER runs it, offline, deliberately.
- **No change to `purge`/tombstone semantics, content-addressing, or raw-is-sacred.**

## 10. Stop-and-raise conditions

- **The append-only re-key admissibility (Q3)** — if the owner has not ruled that `versions` admits an
  owner-gated `migrate_rekey_doc_id`, **park Item 14** with re-entry = that ruling (surfaced §11 / at
  blessing); do NOT relabel an append-only store on inference. (Item 13 preview + Item 15 minter can
  still be built.)
- **The Logseq `id::` insertion format is ambiguous** on a real vault sample (page-properties position,
  an existing properties block, front-matter interplay) → **STOP and raise a `codebase` finding**; never
  guess a format that could corrupt an authored note. Byte-preservation is non-negotiable.
- **A minted id collides** with an existing id, OR a note's `history(minted_id)` is already non-empty
  (an id reused across notes) → **refuse and raise**; never merge two lineages.
- **The daemon is up** when the migrator is invoked → **refuse** (fail-closed); the run is offline-only.
- Any vault write the plan did not scope (beyond the single `id::` line), or any repo-file write → must
  not. Any blessing flip → must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| **Append-only `versions` admits an owner-gated re-key?** (invariant-adjacent — OWNER RULES at blessing) | **Yes** — an `OwnerDeclaration`-gated `migrate_rekey_doc_id` that relabels `doc_id` preserving `(seq, digest, at)`; a relabel, not a history rewrite (precedent: `catalog.relabel_provenance`) | (a) an alias/indirection store mapping old→new doc_id, leaving history untouched (rejected: complicates every version query forever, for a one-time event); (b) rebuild the whole `versions` table under new keys (rejected: same UPDATE semantics, more blast, no gain) | owner rules at `proposed → ready`; if declined, re-graduate toward (a) |
| uuid scheme | `uuid4` (Logseq's own convention) | content-derived id (rejected: a revert would repeat it — not identity-stable); sequential (rejected: not globally unique across vaults/merges) | — |
| Repo docs (design-notes/findings) in scope | **Skip** — they carry YAML `id:` already; minter skips any stable-id note | mint a `id::` into them too (rejected: redundant + they're not the version-store's identity surface) | the owner points the vault at repo docs AND wants them re-identified under `id::` |
| Strip property lines from embedded text | No (consistent with today — properties are already embedded) | strip `id::`/props before embedding (deferred: a separate ingest change, out of scope) | a measured retrieval-quality regression from property noise |

## 12. Dependency & ordering summary

Blast-radius order (read-only → reversible-with-backup → the corpus write): **Item 13** (dry-run
preview, pure read) → **Item 14** (the store re-key primitive, reversible via store backup, owner-gated)
→ **Item 15** (the vault minter, the corpus write, reversible via vault backup) → **Item 16** (the
owner-facing offline orchestration + the no-fork / post-rename-stability / idempotency / fail-closed
verification). All share `core/ingest/mint_ids.py` → one session, not parallel. **`depends_on: bp-031`**
(the `doc_id` decoupling + `id::` resolution must exist first). Model: **opus/high** — highest blast
(the first corpus write + the first append-only relabel), reversibility-critical, invariant-adjacent
(the Q3 owner ruling). The migration RUN is **deploy-coupled** (daemon down; finding-0066), owner-fired,
never in-session. **Item numbering continues the family (13–16).** _(Numbering note: this claimed bp-034;
the diagnostic subcommand shifts to bp-035.)_

---
type: design-note
id: dn-vector-membership-store
track: code-ingest
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-23
updated: 2026-07-27      # adversarial-panel revision pass (§0.1)
links:
  - docs/findings/finding-0168.md                      # the warrant — FIVE owner rulings, verbatim (addendum 4: rename-as-membership-edge)
  - docs/findings/finding-0167.md                      # the interim reuse port this subsumes; its owed L1 line-header check discharges in D0
  - docs/findings/finding-0164.md                      # corpus-wide keep-and-link (notes-lane adoption path)
  - docs/brainstorms/strip-headers-from-the-atom-hash.md   # the owner's identity ruling (2026-07-27) — D0's warrant
  - docs/design-notes/temporal-code-corpus.md          # partially superseded (D1/D2 row model — see §6, incl. two re-homes)
  - docs/design-notes/integrator-densification.md      # consumer: slot-lineage edges join the composed graph
  - core/kernel/stores/sourceset.py                    # the axiom this completes (overlapping sets) — post-K1 path; the first draft cited the pre-move path
  - core/stores/versions.py                            # C1 — content-keyed identity cannot hold a revert linearly; §4 and D2 now obey it
supersedes: dn-temporal-code-corpus D1/D2 row model (digest-stamped duplicated rows)   # PARTIAL — keep-and-link, commit_diffs design, current-view default STAND; §6 records two mechanism re-homes
warrant: docs/findings/finding-0168.md
adversarial_review: "COMPLETED 2026-07-27 — core BLOCK · math BLOCK · systems RATIFY-WITH-AMENDMENTS; every finding dispositioned in §0.1; revised same day; ratification remains owner-only"
---

# Design note — the vector membership store

> A point is a point — geometry, assertion-free. Meaning lives in **membership** (who contains
> it), history in **lineage** (which occupancy chains pass through it). The vector plane is a
> growing, append-only dictionary of idea-atoms; the corpus is the usage record over it. Git's
> content-addressed model, one level down: `digest` = blob sha at file grain, `content_hash` =
> chunk sha at idea grain — hashed over the **header-free body**, because a filename is mutable
> and identity must survive a rename (D0).

## 0. Provenance & mode

Fable design pass, in-session (owner-directed, 2026-07-23); adversarial-panel revision pass
2026-07-27 (§0.1). Warrant **finding-0168** — **five** owner rulings, one thread: (1) vectors are
the versioned entities, stored once; (2) succession is a property of the `(path, slot)` occupancy
chain, never of the vector; (3) the plane is append-only, no machinery deletes; (4) membership
cardinality n(v) and its distribution are first-class observables; (5) **a rename mints no vector
— only a membership edge** (addendum 4, 2026-07-25, `finding-0168:135-188`), which raised
edit-stable chunk identity from cleanup to **load-bearing** and is the spine of D0 — the first
draft predates the addendum and had orphaned it. Grounded against the live bp-099 store model
(whose duplication this removes) and the `commit_diffs`/chains machinery (`ops/code_lineage.py`
— shipped, but **never successfully run**; §0.1 S2).

### 0.1 Adversarial review record (the pre-ratification gate, 2026-07-23 ruling)

Three seats, 2026-07-27: **core BLOCK · math BLOCK · systems RATIFY-WITH-AMENDMENTS.** The owner
ruled the central defect the same day (header-free identity; the linked brainstorm carries the
ruling verbatim and its reasoning). Every panel finding is dispositioned below. All empirical
figures in this note were **re-derived in this revision pass** — chunkers re-run over all 1,653
ledger versions, every store opened read-only, every `file:line` re-opened — not inherited from
the panel (docs/brainstorms/the-unchecked-claim.md: cite primary or mark the hop).

| # | finding | disposition |
|---|---|---|
| C1 | revert breaks D2 idempotence + §4 total order; silent D3 corruption | RESOLVED — D2 currency reconciliation; §4 re-keyed on runs (versions.py C1); §8(a)(f) |
| C2 | warrant drift: fifth ruling + finding-0167's L1 check carried nowhere | RESOLVED — §0(5), D0, §8(i) |
| C3 | schema ambiguity: shared table? shed columns' callers? `provenance` omitted | RESOLVED — D1 pins one shared table, row-scoped shed, provenance stays; PD-2 fence |
| C4 | stale sourceset link; "backfill machinery STANDS" overstated | RESOLVED — links fixed; §6 re-homes the probe (triggers alone stand) |
| C5 | ring placement: sqlite is subtracted plumbing; import would demote sourceset | RESOLVED — D3: memberships enter the kernel as data, never as an import (rings.py:36-41) |
| F1 | coordinate headers inside the hash break identity | RESOLVED — D0 (owner-ruled) |
| F2 | "an edit = ≤1 vector insert" falsified by L1 lineno headers | RESOLVED — D0 canonical-windowing pin; measured: insert 10→0 atoms, rename 38→0 |
| F3 | merges break the total order (ledger walks all commits; chains first-parent) | RESOLVED — D4/§4: chain members ⊊ version set; side-branch fibers are chainless members |
| F4 | revert makes the atom view cyclic; file grain drops re-occupancy | atom half RESOLVED (§4 multigraph); file half DISPUTED — adjacent-dedup only, [A,B,A] survives (§4) |
| F5 | memberships' key unstated; set vs multiset unpinned; §4 over-quantified | RESOLVED — D1 key = occupancy coordinates; D6 n_doc/n_occ split; §4 quantifies slotted layers only |
| F6 | parent D5 resolves endpoints "by digest in the vector store" — column dies | RESOLVED — §6 re-home (2): endpoint resolvable ⇔ membership fiber exists |
| S1 | no measured baseline; the inherited "~4–5×" is a file-grain extrapolation | RESOLVED — measured figures installed (D7); the 4–5× claim struck |
| S2 | "`commit_diffs`, already captured" is FALSE — zero tables live | RESOLVED — verified (snapshots db ro, 2026-07-27); §3 makes capture rebuild step 0 |
| S3 | a monolithic rebuild repeats the live wedge failure mode | RESOLVED — D7: checkpointed resumable slices (`jobs.checkpoint`), time-budgeted, no daemon stop |
| S4 | lance physical churn: ~2.4× bloat, no compaction path | design RESOLVED (§3); the bloat figure DISPUTED — 245 MB disk vs ~232 MB raw vector payload |
| S5 | no standing gauge reports embeds-avoided or the dedup factor | RESOLVED — D6/§8(g): `|M|/|V|` + embeds-avoided gauges; post-rebuild falsifier recorded (D7) |
| S6 | backlog ordering; never rerun the old backfill; carry-forward option | RECORDED — §3/D7 ordering guidance (wedge-clearing is an owner op); 13,311-atom seed measured |

## 1. Objective

Replace the per-version duplicated row model with:

1. **One vector row per distinct idea-atom** `(layer, content_hash)` — `content_hash` over the
   **header-free canonical body** (D0) — deduplicated across versions, reverts, files, **and
   renames**. Append-only: a vector, once landed, is permanent.
2. **A membership relation** carrying all occupancy: which `(path, blob_sha)` versions contain
   which atoms, at which slot/lines, and whether that occupancy is current.
3. **Slot-lineage supersession** `(path, slot): hash_i → hash_{i+1}` — derived, never stored as a
   second truth — giving the integrator's composed graph its finest D-fiber, and one that
   **survives `git mv`** (D0's point: lineage correctness under routine work).
4. **The frequency plane**: n(v) counts and the corpus histogram as standing gauges.

Embedding reuse (finding-0167) falls out: landing a version embeds only atoms absent from the
plane. A revert or copy-paste costs zero geometry — metadata only.

### 1.2 Out of scope (non-goals — read deliberately at ratification)

- **No change to keep-and-link semantics, current-view default retrieval, or the flag-less
  posture** — dn-temporal-code-corpus stands except its row model and the two §6 re-homes.
- **The NOTES lane** — adoption is intended (finding-0164's law; one membership machinery) but
  designed when the notes lane temporalizes; this note builds the code lane. PD-2, with the D1
  stratum fence.
- **No stored edge table for slot lineage** — edges stay derived from membership + `commit_diffs`
  (single source of truth; the dn-code-ingest §436-447 doctrine, kept).
- **No ANN/index tuning, no embedder change, no logical pruning** — append-only makes pruning a
  non-feature; purge (D5) is the only removal and it is an owner act, not policy. Physical lance
  compaction (§3) is IN scope — it removes no logical row. `[INFERENCE — housekeeping boundary
  inferred, not ruled]`
- **AMENDED (owner ruling, 2026-07-27):** the first draft's non-goal *"atoms are whatever the
  (unchanged) chunkers emit"* is **struck** — it was the clause forcing the header defect (§0.1
  F1/F2). Its replacement, exactly bounded: identity hashes the header-free canonical body, and
  L1 windows are cut over canonical prose (D0). **No other chunker behavior changes.**
  `[INFERENCE — the ruling pins identity only; the L1 windowing pin is this note's derivation
  from the measured rename probe (D0), for the owner's eye here]`

## 2. Decisions

### D0 — Atom identity: the header-free body (owner-ruled, 2026-07-27)

**`content_hash` = hash of the chunk's CANONICAL body — coordinate headers stripped. Identity
only: embed text may keep headers.** The ruling's reasoning, which outranks the panel's framing
and must be read as the design's spine:

> **A filename is mutable.** With headers inside the hash, a rename or move re-hashes every chunk
> of the file — so every `(path, slot)` occupancy chain through it breaks, on an operation this
> repo performs constantly, in code and in `docs/` alike (the kernel migration alone moved
> `sourceset.py`; this note's own first draft still cited the old path). That is not a missing
> capability — the panel's frame, cross-file dedup unreachable — it is the **lineage guarantee
> failing under routine work**. A membership store whose chains sever on `git mv` cannot serve
> the succession path it exists to enable.

This restores **finding-0168 addendum 4** (rename-as-membership-edge: a rename is same atoms +
a new fiber, and the rename/edit/split/merge/copy taxonomy is membership set algebra). Its
precondition — edit-stable chunk identity, raised there to load-bearing (`finding-0168:176-182`)
— is exactly what D0 supplies; it also discharges finding-0167's owed L1 line-header check
(`finding-0167:37`): same defect, one fix, verified by §8(h)(i).

**Canonicalization per layer (from the chunkers, `core/ingest/code_corpus.py`):**

- **L0a** (`code_ast`): the header `# {path}:{qualname}{signature}` is a strippable first line
  (`:117-123`; oversized slices already window the header-free body and re-prefix, `:121-123`).
  Canonical body = the text minus that first line. Nothing semantic is lost — the `def` line is
  part of the symbol's own source lines.
- **L0b** (`code_text`): raw-source windows, headerless by construction (`:150-157`). Canonical
  body = the text, unchanged.
- **L1** (`codedoc`): headers are INTERLEAVED — one `# {path}` / `# {path}:{qualname}` /
  `# {path}:{lineno}` line per docstring/comment item, and the joined prose is then windowed
  (`:166-178`). Stripping at hash time alone is NOT enough: window boundaries are computed over
  the header-bearing prose, so a rename that changes path length (nearly all of them) recuts
  windows — measured: a rename still mints **7** L1 atoms under strip-at-hash-only, vs **38**
  under the old identity. **Pin: L1 windows are cut over the CANONICAL (header-free) prose**;
  the canonical window is both identity input and embed body, prefixed for retrieval context by
  a single `# {path}` line (a strippable prefix, exactly the L0a shape; per-item linenos live in
  memberships, not in the text). Under this pin a rename mints **0** atoms and a one-line
  top-of-file insert mints **0** (vs **10** today) — measured over the real chunkers,
  2026-07-27, on live blobs.

**Consequence, named:** identity now differs from embed text, so a shared atom's stored
`text`/`vector` is its FIRST-LANDED rendering (an L0a prefix may carry another occupancy's path).
Coordinates for display always resolve from memberships, never from the stored text; the
retrieval effect of representative renderings is a T4 falsifier (R7).

### D1 — The split: geometry / reference / history

Three stores, one truth each:

- **`vectors` — the existing LanceDB `chunks` table, evolved in place**
  (`core/stores/vectorstore.py:24`): one shared table, ONE ANN search — never a code-only fork.
  One row per atom: `id = "{layer}:{content_hash}"`, `layer`, `text`, `vector`, **`provenance`
  (STAYS on the row — the MIRROR firewall is a row prefilter, `vectorstore.py:317-324`, and holds
  only if the column is there to filter)**, and the existing `current` column re-read as
  **`current_any`** (does ANY current membership contain this atom — the cheap default
  prefilter). Note rows keep their vacuous `current=true`, so the D3 default `current = true`
  clause (`:320-321`) serves both lanes unchanged. Identity is `(layer, content_hash)`;
  **one-layer-one-provenance is carried as a test invariant, so an atom never spans strata** —
  the PD-2 fence: cross-stratum sharing would break both the prefilter and sourceset's
  one-stratum axiom (`core/kernel/stores/sourceset.py:58-62`), so it is unrepresentable until
  PD-2 re-designs that boundary. **The occupancy columns (`source_path`, `digest`, `qualname`,
  `line_*`, `chunk_index`) are shed from CODE-ATOM ROWS, not from the schema**: note rows still
  carry them and every prose-lane consumer is untouched — `index_amendment`/`delete_source` are
  `source_path`-scoped and never match an atom row's empty path (`core/ingest/index.py:87`);
  `group_sources` keys on `digest` (`sourceset.py:131`), and CODE consumers reach source objects
  through membership fibers (D3), never through group-by-digest, so no shed row enters it. No
  `tombstoned` flag on vectors — purge DELETES the row (D5); the tombstone record lives on
  memberships.
- **`memberships` (SQLite, beside the vault catalog; home `core/stores/` — outer ring, never
  imported by kernel code, D3)** — one row per occupancy, **key = the occupancy's coordinates
  `(path, blob_sha, layer, chunk_index)`** (derivation is a pure function of `(path, source)`,
  `code_corpus.py:181-194`, so `chunk_index` is well-defined and re-derivable), columns
  `content_id`, `slot`, `line_start`, `line_end`, `current`, `tombstoned`. **Multiset honesty
  (the F5 pin): two identical windows in one blob are two rows with distinct `chunk_index`** —
  no occupancy vanishes by key collision; the two n(v) readings are D6's. `slot` = qualname for
  **L0a only**: as built, L1 chunks carry `qualname=''` exactly like L0b (`code_corpus.py:177`),
  so L0a is the only slotted layer; L0b and L1 are membership-only, honestly chainless (R4).
  A version's projection = the fiber `M(path, blob_sha)`.
- **History** — derived: per-`(path, slot)` occupancy chains from memberships ordered by the
  first-parent blob chain; supersession edge where consecutive runs differ (§4 for the
  revert/merge-correct formulation). Source: **`commit_diffs` — designed at the parent, shipped
  in `ops/code_lineage.py`, and NEVER successfully captured: the live snapshots db has zero
  `commit_diffs`/`_commit_diffs_captured` tables (verified read-only, 2026-07-27; the one
  capturing job, 300240, died in `TimeoutError` on 2026-07-25).** The rebuild captures it as
  step 0 (§3). Materializable as a view; never a second store.

Provenance is unchanged (CODE minted structurally — `code_corpus.py:220` hardcodes it; the MIRROR
firewall holds BECAUSE the `provenance` column stays on atom rows — designed above, not asserted).

### D2 — Landing a version (the write path)

`land(path, blob_sha, chunks)`: (1) compute canonical `content_hash` per chunk (D0); (2) **insert
only the atoms absent from the plane** (the embed step — everything else is reuse by
construction); (3) write the membership fiber for `(path, blob_sha)`; an existing fiber's rows
stand (fiber equality holds because derivation is pure); (4) **currency reconciliation — NEVER
skipped, even when step 3 was a no-op**: set `current=true` on exactly the fiber whose blob is
the path's HEAD blob and `current=false` on the path's every other fiber. Re-landing is
idempotent BECAUSE reconciliation converges, not because the call short-circuits — the first
draft's "existing fiber ⇒ no-op" was precisely the C1 bug `core/stores/versions.py:22-27`
documents (content-keyed identity cannot hold a revert): on A→B→A the fiber for blob A already
exists with `current=false`, and a short-circuit leaves **B** current — silent D3 corruption.
§8(a) reddens on exactly that lander. (5) maintain `current_any` on atoms whose
current-membership count crossed 0↔1.

Write amplification, measured (the F2 correction — the first draft's "an edit = ≤1 vector
insert", inherited from finding-0168's idealization, is struck as false at chunk grain): a
coordinate-only change — rename, move, line shift — is **0** inserts (D0, measured); a content
edit inserts the changed atoms (L0a: the edited symbols' slices; a prose edit may additionally
recut downstream L1 windows — inherent to any sliding window, bounded by the windows downstream
of the edit, and no longer triggered by coordinates at all).

### D3 — Retrieval (the read path)

ANN search over `vectors` (prefilter: the existing `current = true` clause read as `current_any`,
plus provenance — `vectorstore.py:317-324`; `include_superseded=True` lifts it) → top-k atoms →
**join memberships** to resolve occupancies `(path, blob, slot, lines, current, tombstoned)`. One
atom may resolve to several occupancies — that is the FEATURE: a hit natively answers "this idea
lives in versions v3–v7 of X and also in Y" (the atom's reach). Default consumers see current
occupancies only — flat retrieval behavior preserved.

**The sourceset seam (the C5/ring pin):** `sourceset` lives in the kernel
(`core/kernel/stores/sourceset.py`) and sqlite3 is subtracted plumbing
(`core/kernel/rings.py:36-41`), so the membership store must never be reached by kernel import —
that import would mechanically demote sourceset from the fixed point. Memberships enter the
kernel **as data**: rows through the existing `RowSource`-shaped protocol (`sourceset.py:48-55`),
store resident in `core/stores/`. The group-by-digest axiom completes as "source object = its
membership fiber" — handed in, never imported. If the seam cannot stay data-shaped, that is a
finding, not an import.

### D4 — Fork/join/merge semantics (ruled; the formal pin)

**Supersession edges live on slot-lineages, never on vectors.** A vector shared by two files =
one atom, two memberships. An edit in one file mints an edge on ITS `(path, slot)` chain and
swaps ITS membership; the other file's chain passes through the original untouched. Forks,
parallel same-edits (same endpoints, distinct chains), and convergence (a later copy-paste
re-shares the atom) are all **graph facts** — two lineages intersecting at a node — never stored
claims. Edge identity: `(path, slot, old_hash → new_hash, at blob transition)`.

**Merges (the F3 pin):** chains are FIRST-PARENT (`ops/code_lineage.py:85-95`), while the
snapshots ledger walks ALL commits (`ops/code_snapshot.py:358` — `rev-list --reverse HEAD`). So a
side-branch version — a worktree branch editing a path over ≥2 commits, then merging; this repo's
routine delegation workflow — is a ledger version and lands a fiber, but sits on NO chain:
**chain members are a strict subset of the version set, and chains stay linear** (never posets).
A side-branch fiber's atoms are reachable through membership; its lineage enters history only via
the first-parent delta at the merge commit. §4 quantifies edge invariants over chain members, not
over all fibers.

### D5 — Append-only + the purge exception (ruled)

No machinery delete exists in the API surface (the store exposes no vector delete; supersession
flips memberships). The ONE removal is **purge** (finding-0164, owner-gated, privacy outranks
lineage): delete the vector row, set `tombstoned` on its memberships — a recorded hole, never
silent. Near-moot for CODE (public in git); load-bearing when notes adopt this model.

### D6 — The frequency plane (ruled)

**Two counts, both first-class, never conflated (the F5 pin):** `n_doc(v)` = distinct current
paths holding v — the document-frequency/IDF reading, immune to within-file repetition, and the
histogram's default; `n_occ(v)` = membership rows — the multiset reading, where L0b's repeated
windows count. Both current-cut and lifetime variants are defined and cheap. Standing gauges:
the **n_doc(v) histogram** per lane and over time — Zipf-shape conformance is a falsifiable
corpus property (deviation localizes something real: boilerplate consolidation, vocabulary flux)
— **plus the dedup factor `|M|/|V|` and embeds-avoided per landing** (the S5 amendment; `|M|/|V|`
IS the dedup factor, so the D7 falsifier stays observable forever). Consumers: IDF-style
retrieval weighting (or its deliberate inverse — idiolect mining), code-idiom detection,
hub-degree for the dreamer, fork-in-high-n as a signal event, and addendum 4's `~1/n(v)`
weighting of rename-overlap evidence. Home: an ops/eval gauge beside the drift-gauge family;
joins the T4 limits work.

### D7 — Migration: one rebuild — measured, sliced, resumable

Vectors are derived and regenerable (§8 doctrine; `reset` exists). **The measured baseline
(re-derived 2026-07-27, this pass: real chunkers over all 1,653 ledger versions, stores opened
read-only). The first draft's "~4–5×" was finding-0168's FILE-grain figure (1,653 versions / ~257
files ≈ 6.4×) extrapolated to chunk grain — an unchecked claim, struck:**

| figure | measured value |
|---|---|
| live store | 22,621 rows / 16,761 distinct `(layer, text)` = **1.35×** duplication today |
| backfill state | `_code_corpus_backfilled` = 0 rows; the ONE attempt failed (job 300240, `TimeoutError`, 2026-07-25) |
| full history, duplicated model | **52,755** embeds (Σ per-version chunks) |
| full history, membership + D0 | **22,502** atoms = **2.34×** (L0a 2.54× · L0b 2.05× · L1 2.42×) |
| identity counterfactuals | headers-in-hash: 25,728 = 2.05× · strip-at-hash-only: 23,432 = 2.25× — the L1 windowing pin is what D0 buys |
| carry-forward seed | **13,311** atoms (7,791 L0a + 5,520 L0b) already embedded live with embed text unchanged — vectors reusable |

**The post-rebuild falsifier, recorded:** on the 2026-07-27 ledger cut the rebuild must land
≈ 22,502 atoms against the duplicated model's 52,755; like-for-like deviation beyond ~10% is a
finding, not a shrug. "Strictly fewer embeds (|atoms| ≤ Σ chunks)" is kept as an invariant but is
NOT acceptance — it holds vacuously at zero savings (the false-success shape); the measured
factor is the claim under test (§8 g).

The migration is ONE deliberate rebuild, **run as checkpointed, resumable queue slices — never a
monolith**: the job class it enlarges is exactly the one wedged now (`code_sync` job 300246
`running` since 2026-07-25T03:45 with 1,766 jobs queued behind it; enqueues ceased 04:06), so the
rebuild runs as BACKGROUND jobs with `jobs.checkpoint` resume tokens and a per-slice time budget,
respecting single-writer as a queue citizen — no daemon stop. Ordering (S6, recorded as guidance;
clearing the wedge itself is an owner op): clear the wedge → drain the backlog → **step 0:
capture `commit_diffs`** (§3) → sliced rebuild → compaction (§3). **The old duplicated backfill
must never be run** — 52,755 vs 22,502 embeds is 2.34× measured waste. The carry-forward seed:
the 13,311 L0a/L0b atoms above enter by canonical re-hash of stored rows at zero embed cost
(~59% of the atom set); **L1 recuts under D0's windowing pin and re-embeds** (3,424 atoms) — its
stored windows were cut over header-bearing prose and do not survive. Owner-visible
(`palace code-rebuild`, the code-seed shape), with the re-homed incompleteness probe (§6) for
auto-catch-up thereafter. Note rows (prose) migrate vacuously or stay on the old path until PD-2
— builder settles which is mechanically smaller.

### D8 — Crash consistency (the one real systems risk)

Order of writes: vector inserts FIRST (append-only, unreferenced-is-harmless), membership fiber
SECOND (transactional in SQLite), currency reconciliation + `current_any` maintenance LAST
(re-derivable from memberships — a repair pass exists). An orphan atom (inserted, fiber write
crashed) is dormant geometry — the idempotent re-land repairs; nothing dangles by reference.
Membership SQLite is the reference truth; `current_any` is a cache with a rebuild path.
Reconciliation (D2 step 4) is itself convergent, so a crash between fiber write and currency
flip is repaired by any later land or by the repair pass.

## 3. Wiring & enablement (required §)

Flag-less (the standing rulings): this is the store's semantics, not a feature. Ships as the code
lane's store vNext; `sync()`/`backfill()` land through D2 unchanged in their triggers (the bp-098
wiring — housekeeping gate, `code-seed`, `code-backfill`, the catch-up probe — triggers stand;
the probe's data source re-homes per §6). The enable act is the D7 rebuild: `palace
code-rebuild`, owner-visible, sliced (D7), **step 0 = the first successful `commit_diffs`
capture** (`ops/code_lineage.py:112-130` — shipped, unrun; §0.1 S2). The n(v)/`|M|/|V|` gauges
register beside the existing gauges (read-only, cheap).

**Physical maintenance is part of the store's semantics (S4):** the lance dataset accumulates a
version per write batch — 298 dataset versions, 245 MB on disk, measured 2026-07-27. Against
~232 MB of raw vector payload (22,621 rows × 2560 dims × 4 B) today's bloat is modest — the
panel's ~2.4× figure did not survive re-measurement — but `current_any` flips are lance updates
that rewrite fragments, and D2 makes them routine. Pin: `current_any` stays in lance (the ANN
prefilter needs it, `vectorstore.py:317-324`); flips are batched per landing (only atoms crossing
0↔1 — typically zero to few rows); the rebuild ends with compaction + old-version cleanup; and
housekeeping runs cleanup on cadence. No compaction path exists in `vectorstore.py` today
(verified) — building one is in scope; if the shim lacks the API, that is a finding at build.

## 4. Math carried explicitly

Let V = atoms (append-only: V(t) monotone ↑), O = occupancies, membership M ⊆ V × O; a version is
the fiber M(path, blob); Σ fiber sizes = |M|. **Occurrence keying (the C1 lesson,
`core/stores/versions.py:22-27` — content identity cannot hold a revert; position identity can):**
for each slotted `(path, slot)` (slotted = L0a only, D1), walk the path's FIRST-PARENT blob chain
(D4) and collapse adjacent equal occupants into RUNS r₁ … r_k. The runs are the occurrences;
supersession edges are the consecutive-run pairs (hashes differ by construction): per slot
**|edges| = |runs| − 1** — correct under reverts (A→B→A: runs A, B, A → 3 runs, 2 edges; the
first draft's per-slot total order over *distinct* occupants was false exactly there). The
occurrence graph is a disjoint union of chains — a forest. **Its projection onto atoms is a
directed MULTIGRAPH, not a DAG** (the F4 correction): A→B→A projects the 2-cycle h_A→h_B→h_A —
an atom-cycle IS a re-occupancy, readable as such; forks/joins are the intersections (D4). File
grain agrees: `supersession_chains` collapses only ADJACENT repeats
(`ops/code_lineage.py:151-156`), so [A, B, A] is preserved and a revert stays visible — the
docstring's "ordered distinct sequence" (`:139`) is loose language, not the behavior (the F4
file-grain claim is disputed on the code). Chain members ⊊ ledger versions (D4): a chainless
side-branch fiber contributes to M and to n(v) but to no edge count. Invariants to carry as
tests — each exercised on the §8(f) fixture (a revert, a merge side-branch, a shared atom, a
duplicate L0b window pair), never on a corpus that satisfies them vacuously: per-slot |edges| =
|runs| − 1; Σ fiber sizes = |M|; `current_any(v) ⇔ n_doc(v, t) > 0`; append-only ⇒ no test may
ever observe |V| decrease (except across a logged purge). Histogram: the rank-frequency plot of
lifetime n_doc(v); Zipf conformance checked in T2/T4, not assumed.

## 5. Risks

- **R1 crash consistency** (D8): mitigated by write order + convergent reconciliation + repair
  pass; property test required (§8 e).
- **R2 join latency on the read path**: top-k membership joins are k×small SQLite lookups;
  measure in T4 before optimizing; the `current_any` prefilter keeps the ANN set lean.
- **R3 `current_any` drift** (cache vs truth): the repair pass + a ratchet comparing flag vs
  membership counts on a sample.
- **R4 L0b AND L1 slotlessness (corrected)**: as built, L1 windows carry `qualname=''`
  (`code_corpus.py:177`) — **L0a is the only chained layer**; L0b and L1 are membership-only.
  Accepted and honest; per-item L1 chunking that would give L1 chains is PD-5, never a quiet
  re-slot.
- **R5 migration scope creep**: the rebuild touches only code rows; note rows explicitly parked
  (PD-2) — the builder must not "helpfully" migrate prose.
- **R6 rebuild wedging the lane**: the live failure mode (D7); mitigated by slicing + budgets;
  falsifier: any slice exceeding its budget without a checkpoint.
- **R7 representative renderings** (D0): a shared atom's stored text/vector is first-landed; if
  T4 shows retrieval loss attributable to header prefixes, revisit the embed-text rule —
  identity is untouched by that revisit.

## 6. Supersession declaration (for the owner's ratification hand)

Partially supersedes **dn-temporal-code-corpus**: D1/D2's ROW MODEL (digest-stamped rows
duplicated per version; `current` on vector rows) → this note's atom+membership split.
Keep-and-link semantics, history embedded, the `commit_diffs` design, current-view default, and
flag-less wiring all STAND — **with two mechanism re-homes the owner banners at ratification**
(each cited to the parent's own text, which a shed column would otherwise silently break):
(1) the §3 incompleteness probe reads "the store's distinct code-digest count"
(`temporal-code-corpus.md:141-143`) — that column leaves atom rows, so the probe re-homes to the
membership store's distinct `(path, blob_sha)` fiber count (the same number, sturdier home); the
backfill TRIGGERS stand unchanged, the probe's data source does not. (2) D5's supersession-edge
endpoints "resolvable **by digest in the vector store**" (`temporal-code-corpus.md:125-126`)
re-home to fiber existence: endpoint resolvable ⇔ `M(path, blob)` is non-empty (F6).
finding-0167's mechanical port is subsumed (do not build it separately if this ratifies first),
**including its owed L1 line-header check — discharged by D0 and verified by §8(i).**

## 7. Parked decisions

| PD | Decision | Default recorded | Re-entry condition |
|---|---|---|---|
| PD-1 | cross-file dedup scope | RULED IN (owner) — one atom, n memberships, fork semantics | — (closed at capture) |
| PD-2 | notes-lane adoption | code-first; prose untouched by D7; atoms never span strata (D1 fence) | notes keep-and-link lands (f-0164) AND the prefilter is redesigned for sharing |
| PD-3 | materialized slot-edge view | derived on read | a consumer needs edge queries at a rate joins can't serve |
| PD-4 | IDF-weighted retrieval | gauge only, no ranking change | a retrieval-quality experiment (T4) shows lift |
| PD-5 | L1 slotting | L1 stays windowed + slotless (R4) | a consumer needs docstring/comment lineage — then per-item L1 chunks, a deliberate re-chunk |

## 8. Acceptance shape (for graduation)

Every criterion names the **degenerate input** on which it would pass without testing its claim,
and requires the check to redden on it (docs/brainstorms/the-false-success-rule.md, owner-agreed;
the first draft's (a) and D7 inequality were both offenders).

- **(a) Revert — the C1 case.** Land A → B → A (a real `git revert`). Zero vector inserts, zero
  new membership rows, AND currency converges: A's fiber `current=true`, B's `current=false`.
  *Degenerate input:* a do-nothing lander also lands zero vectors — so the currency assertions
  are mandatory, and a lander that short-circuits on "fiber exists" (the first draft's rule)
  reddens by leaving B current.
- **(b) Fork.** Precondition ASSERTED first: the shared atom has 2 current memberships and
  |V| < Σ chunks. *Degenerate input:* a store that never dedups makes "the other file's fiber
  untouched" vacuous — it reddens at the precondition. Then: edit one file → exactly 1 new atom,
  1 membership swap, the other fiber byte-identical; both lineages traverse the shared node.
- **(c) Append-only.** No code path deletes a vector (API-level) except purge — and purge must
  OBSERVABLY act: row gone, memberships tombstoned. *Degenerate input:* a purge that silently
  no-ops also "never deletes"; the criterion asserts the recorded hole exists.
- **(d) Retrieval.** Fixture holds ≥1 superseded occupancy. *Degenerate input:* an all-current
  store passes any current-filter vacuously — reddens at the fixture precondition. Default
  search returns only current occupancies; `include_superseded` surfaces the superseded one; a
  shared atom resolves to all its current homes.
- **(e) D8 property test.** Crash injected between vector insert and fiber write; the test FIRST
  asserts the orphan state is observable (*degenerate input:* a "crash" injected after all
  writes makes repair vacuous), then re-land repairs, nothing dangles.
- **(f) The §4 invariants as tests** — on the degenerate fixture (a revert, a merge side-branch
  version, a shared atom, a duplicate L0b window pair); each invariant reddens under a seeded
  violation, and the load-bearing gates get a mutation check (the companion rule).
- **(g) The rebuild falsifier.** On the 2026-07-27 ledger cut: ≈ 22,502 atoms vs 52,755
  duplicated embeds (D7); like-for-like deviation > ~10% is a finding. *Degenerate input:*
  "|atoms| ≤ Σ chunks" alone holds at zero savings — the measured factor is what is asserted.
  The standing gauge renders `|M|/|V|` and embeds-avoided per lane (D6).
- **(h) Rename — the spine.** Rename an embedded file (same blob): **0** new atoms, 1 new fiber,
  the old path's fiber `current=false` (measured: 0 under D0; 38 under the old identity — the
  check reddens against any hash that still eats the path). *Degenerate input:* renaming a
  never-embedded file mints 0 trivially — the precondition asserts the atoms pre-exist.
- **(i) L1 edit stability — finding-0167's check, discharged.** Insert one line at the top of a
  file whose prose items span ≥2 L1 windows. *Degenerate input:* a file with 0–1 prose items
  passes vacuously — the fixture precondition reddens on it. **0** new `codedoc` atoms
  (measured: 0 under D0's windowing pin; 10 raw; and >0 under strip-at-hash-only when a recut
  bites — the pin, not the strip, is what this tests).

Graduation: likely two session-plans (store+land+read; rebuild+gauges+probe+compaction) — split
at /graduate against the then-current tree.

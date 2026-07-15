---
type: build-plan
id: bp-035
status: in-progress
design_ref:
  - docs/design-notes/core-query-protocol.md
contract: builder
write_scope:
  - core/reference_view.py
  - tests/unit/test_reference_view.py
  - tests/integration/test_reference_oracle.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-14
updated: 2026-07-14
links:
  - docs/design-notes/core-query-protocol.md
  - docs/design-notes/temporal-retrieval-algebra.md
  - docs/findings/finding-0059.md
  - docs/findings/finding-0061.md
  - core/stores/reference_edges.py
  - core/ops_view.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — `ReferenceView`: the deterministic reference read surface (the §2.3 archetype)

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Graduated from ratified `dn-core-query-protocol` §2.3 (the reference agent — "the archetype, and the
first build") + §3 Consequence 2 (the reference query surface). The fable pass resolved the surface
shape to a **`ReferenceView` library object** (that note §1.3 item 3) — not an addressable service —
so this plan builds a typed read window in the mould of `OpsView`/`MirrorView`, NOT a new process.

**Read-only, in-core, no model.** The note's whole point (§2.3) is that this is "the simplest
well-typed client — no model, no cross-stratum budget, no firewall composition, no hallucination
surface." An in-core reader of the live reference stratum is NOT a plane crossing (§2.4 item 5: "In-core
clients are unaffected"). Nothing here loosens an invariant. Model tier opus/high — deterministic
engineering over a settled design; **no fable** (the math/design is banked in the ratified notes).

## 1. Objective

Turn the built-but-**agent-unreachable** reference graph into an actual "who cites this?" capability.
`reference_edges.sqlite` holds ~272k edges (incl. ~73k `corpus_to_corpus`), but its only readers today
are the *writer* (`ops/code_sensor.py`) and *reset* (`launcher.py`) — the `all(target_ref=…)` primitive
has **zero agent callers** (`dn-core-query-protocol` §1.1: "code-anchored + agent-unreachable"). Build
`ReferenceView` — a deterministic, fiber-scoped (`F`), commit-anchored read surface: `references_to`,
`references_from`, `connected_set` — and prove it against an **independent repo-grep oracle at HEAD**
(§2.6), turning the finding-0059/0061 staleness anxiety into a measured sensor-fidelity number.

## 2. Context manifest

Read whole, in order:

1. `core/stores/reference_edges.py` — the substrate. `ReferenceEdgeStore` (`:252`); the read API
   `all(*, direction, ref_type, source_ref, target_ref)` (`:282`), `for_commit(commit_sha)` (`:312`),
   `count()` (`:318`); `open_reference_edge_store(config)` (`:336`); the `ReferenceEdge` dataclass
   fields (from `_row` `:322` + the DDL `:116`: `edge_id, commit_sha, ref_type, source_kind, source_ref,
   source_detail, target_kind, target_ref, target_detail, source_line, created_at`); `REF_TYPES` (`:102`),
   `KINDS`/`DIRECTIONS` (`:106-107`). **Edges are per-commit** — the "current" scoping question (§3 Q1).
2. `core/ops_view.py` — `OpsView.over(attestations, ledger, *, drift=…)` (`:78`): the READ-ONLY-window
   pattern to mirror (bind the store's reader methods; the returned view exposes those and only those,
   the mutators unreachable). `ReferenceView.over(store, *, commit)` follows this exactly.
3. `ops/code_sensor.py` — `_corpus_to_corpus_edges` (`:427`) + `_mint_reference_edges` (`:383`): the
   sole WRITER, and the reference-*identification* the view reads back (front-matter grammar + inline
   citations + wikilinks). Confirms the corpus_to_corpus edges exist and how they're keyed (§4).
4. `ops/lifecycle/runs.py` — `RunLedger.last()` (`:130`) → the active run's `commit_sha`: the anchor
   for "current" (§3 Q1). `git_state(repo_root)` in `ops/lifecycle/launcher.py` gives HEAD as a fallback.
5. `docs/design-notes/core-query-protocol.md` §2.3 (the archetype), §2.6 (the self-grading loop + the
   three disciplines: grep-not-store oracle, golden-set firewall, the φ_ref record), §2.1 (the View is a
   partial scope instance — do NOT build the general scope type system here; §9 non-goal).
6. `tests/integration/test_reference_edge_isolation.py` — confirms the store is balance-isolated; the
   view must preserve that (it reads, mints nothing, imports nothing from `core/complex`/`core/temporal`).

## 3. Investigation & grounding

- **Q1 — What is the "current" citation set, given per-commit edges?** `reference_edges` accumulates one
  row per (edge, commit) — `commit_sha` is part of identity (`reference_edges.py:118-120,142`), so the
  same citation at two commits is two rows and `all(target_ref=X)` returns edges across ALL history
  (~272k total). **The code does NOT settle which commit is "now."** What would: the reference sensor
  re-projects per commit, so the current truth is the edges at the *latest projected* commit. This plan
  pins **`ReferenceView.over(store, *, commit)`** — the view filters to one anchor `commit`; a factory
  `open_reference_view(config, *, commit=None)` resolves the default to the **active run's `commit_sha`
  (`RunLedger.last()`), falling back to `git HEAD`** (`git_state`), matching the §2.6 oracle's "at HEAD."
  Recorded as a parked decision (§11) with the rejected alternative (union-across-history).
- **Q2 — What are "fibers `F`"?** The note (§2.2) types `F` = citations/warrants (the reference edges),
  `D` = supersession (dispositional, a DIFFERENT store — `versions`/the temporal `boundary.py`). The
  reference store holds ONLY `F` edges — so "fiber-scoped" is automatic here; there is no `D` in this
  store to exclude. The view is `E = {F}` by construction (§2.1's "`D`-exclusion is a type constraint" is
  free — the type simply cannot name `D`). `[grounds: reference_edges.py is citation-only; supersession
  lives in core/temporal/boundary.py + the version store, never here.]`
- **Q3 — Is the surface reachable today?** No. `grep` for readers of `open_reference_edge_store` →
  `code_sensor.py` (writer) + `launcher.py` (reset) only; `all(target_ref=…)` has zero callers outside
  the store's own docstring. This plan is the first reader. `[Explore-verified 2026-07-14.]`
- **Q4 — connected_set semantics.** §2.3: "given a target, return its connected set over fibers `F`, at
  fixed time." A bounded BFS over the citation graph at the anchor commit: `references_to`∪`references_from`
  frontier expansion to `depth` hops, returning the set of reached doc/code refs with the edges that
  reached them. Deterministic; `depth=1` is the common "direct citations" case. No model.
- **Q5 — The oracle (§2.6).** The self-grader greps the repo at HEAD for citations (front-matter
  `design_ref`/`links`/`depends_on`/`warrant`/`supersedes`, inline `[[wikilink]]` + `dn-*`/`finding-*`
  note-citations, backticked `*.py` path-mentions) and diffs against `ReferenceView.references_from(doc)`.
  It measures **sensor fidelity** (recall/precision of the stored graph vs repo reality), NOT the view's
  correctness in isolation — the view is trivially correct over the store; the oracle tests whether the
  STORE matches reality (finding-0059/0061). The note's hand-demo reported doc→doc recall 0/16 at the 61k
  snapshot; with 73k corpus_to_corpus edges now minted, this run re-measures it — a reconciliation datum.

## 4. Reconciliation

- **`dn-core-query-protocol` frontmatter is STALE and its §3.1 first-plan is already satisfied.** The
  note says "reference_edges, 61k edges … code-anchored" and lists "the doc→doc reference extractor" as
  the recommended *first* graduation (§3 Consequence 1). But `ops/code_sensor.py:427`
  (`_corpus_to_corpus_edges`) ALREADY mints doc→doc edges (front-matter + inline + wikilink), and the
  store now holds ~272k edges incl. ~73k corpus_to_corpus. **Proposal (cross-reference-on-extension, NOT
  a silent edit):** file a `spec-fidelity` finding recording that §3.1's extractor is built (by the
  sensor, post-note-snapshot) so the real first plan is THIS read surface (§3 Consequence 2), and the
  note's "agent-unreachable" is the standing gap this plan closes. The ratified note is immutable (A8) —
  the finding is the channel; the orchestrator batches any note-erratum to the owner. **This plan edits
  the note nowhere.**
- No code is corrected/replaced — this is purely additive (a new read window). `code_sensor` (writer),
  `reference_edges` store, and `core/temporal` are untouched.

## 5. Write scope

`core/reference_view.py` (the new `ReferenceView` library object + `open_reference_view` factory),
`tests/unit/test_reference_view.py` (the view's read methods + connected_set over in-memory fixtures),
`tests/integration/test_reference_oracle.py` (the §2.6 repo-grep differential oracle over the live store).
**Deliberately OUT of scope:** `core/stores/reference_edges.py` (READ unchanged — the view wraps its
existing API; if a `latest_commit()` read is wanted it is a follow-on, see §11), `ops/code_sensor.py`
(the writer/extractor — untouched), `core/temporal/**` (the algebra — a separate consumer, not wired
here), the general capability-scope type system (§2.1 — a later graduation, §9), every store/design
note, and the denylist.

## 6. Interfaces pinned inline

```python
# core/reference_view.py — the NEW surface (mirror OpsView.over's bind-the-readers pattern).

from dataclasses import dataclass
from core.stores.reference_edges import ReferenceEdge, ReferenceEdgeStore

@dataclass(frozen=True)
class ReferenceView:
    """A deterministic, fiber-scoped (F), commit-anchored read window over the reference graph.
    Exposes reads and only reads — the store's add_batch is unreachable through it (§2.1 scope)."""

    # bound at .over(): the anchor commit + the store's read closures
    _edges_to:   "Callable[[str], list[ReferenceEdge]]"   # references TO a ref, at the anchor commit
    _edges_from: "Callable[[str], list[ReferenceEdge]]"   # references FROM a ref, at the anchor commit
    commit: str

    @classmethod
    def over(cls, store: ReferenceEdgeStore, *, commit: str) -> "ReferenceView":
        # filter store.all(target_ref=…/source_ref=…) to `commit` (edges are per-commit — §3 Q1)
        ...

    def references_to(self, ref: str) -> list[ReferenceEdge]: ...     # "who cites this doc/symbol"
    def references_from(self, ref: str) -> list[ReferenceEdge]: ...   # "what this doc/symbol cites"
    def connected_set(self, ref: str, *, depth: int = 1) -> set[str]: ...  # bounded BFS over F (§2.3/Q4)

def open_reference_view(config=None, *, commit: str | None = None) -> ReferenceView:
    """Factory: default `commit` = the active run's commit_sha (RunLedger.last()), else git HEAD
    (§3 Q1). Opens the live store read-only and binds a ReferenceView anchored at that commit."""
    ...

# core/stores/reference_edges.py — REUSED unchanged (do NOT edit):
#   store.all(*, direction=None, ref_type=None, source_ref=None, target_ref=None) -> list[ReferenceEdge]
#   store.for_commit(commit_sha) -> list[ReferenceEdge]   # per-commit slice
#   ReferenceEdge fields: edge_id, commit_sha, ref_type, source_kind, source_ref, source_detail,
#                         target_kind, target_ref, target_detail, source_line, created_at
```

## 7. Items

### Item 1 — `ReferenceView` + the read surface
- **Objective:** the commit-anchored read window: `references_to` / `references_from` filter
  `store.all(target_ref=…/source_ref=…)` to the anchor commit; `over()`/`open_reference_view` bind it.
- **Files:** `core/reference_view.py`, `tests/unit/test_reference_view.py`.
- **Acceptance test:** over an in-memory `ReferenceEdgeStore` seeded with edges at two commits,
  `ReferenceView.over(store, commit=C1).references_to("docs/a.md")` returns exactly the C1 edges whose
  `target_ref == "docs/a.md"` (never the C2 rows); `references_from` is the dual on `source_ref`; the
  view exposes no mutator (no `add_batch`/`_conn` reachable) — a `hasattr` assertion.
- **Falsifier:** the view returns edges from a DIFFERENT commit than its anchor (stale-union bug); OR a
  write method is reachable through the view (scope leak).
- **Invariant(s):** read-only (Inv 4 flavor — reports data, takes no action); in-core (Inv 2 unaffected).
- **Touches stored data?** No.  **Parallelizable?** No (Item 2 builds on it).

### Item 2 — `connected_set` (bounded BFS over fibers)
- **Objective:** `connected_set(ref, *, depth=1)` — the §2.3 "connected set over `F`": frontier-expand
  `references_to ∪ references_from` for `depth` hops from `ref`, returning the reached ref-set.
- **Files:** `core/reference_view.py`, `tests/unit/test_reference_view.py`.
- **Acceptance test:** on a fixture chain `a→b→c` (a cites b, b cites c), `connected_set("a", depth=1)`
  = `{b}` (or `{a,b}` incl. self — pin one and test it); `depth=2` reaches `{b,c}` (or `{a,b,c}`);
  cycles terminate (a↔b graph does not loop forever); returns 0 on an unknown ref.
- **Falsifier:** unbounded traversal on a cyclic citation graph (no termination); OR `depth` ignored.
- **Invariant(s):** deterministic, read-only.  **Touches stored data?** No.  **Depends on:** Item 1.

### Item 3 — the repo-grep self-grading oracle (§2.6)
- **Objective:** an INDEPENDENT oracle greps the repo at HEAD for a doc's outbound citations
  (front-matter `design_ref`/`links`/`depends_on`/`warrant`/`supersedes` + inline `[[wikilink]]`/`dn-*`/
  `finding-*` + backticked `*.py` path-mentions) and diffs against `references_from(doc)`, reporting a
  recall/precision fidelity number over a sample of `docs/**`.
- **Files:** `tests/integration/test_reference_oracle.py`.
- **Acceptance test:** the differential harness runs over the LIVE store, computes per-doc recall of
  stored-vs-grepped citations, and asserts a **floor** (e.g. doc→doc recall ≥ a threshold set from the
  first measured run — NOT 100%, since the sensor is precision-gated). The test PRINTS the fidelity
  number (the monitored sensor-fidelity datum, finding-0059/0061) and re-measures the note's 0/16 demo.
- **Falsifier:** the oracle reads the STORE instead of grepping the repo (circular — §2.6 discipline 1);
  OR it asserts exact equality (mistakes precision-gating for a bug).
- **Invariant(s):** the oracle is repo-grep, never the golden set (§2.6 discipline 2; Constitution §9).
- **Touches stored data?** No (reads the store + greps the repo).  **Depends on:** Item 1.

## 8. Math carried explicitly

**N/A — no new mathematical object.** `connected_set` is a bounded graph BFS (deterministic, no
spectral/kernel content); the algebra (X_cite, `L₁`, the operators) lives in `core/temporal/` and is a
SEPARATE consumer of the same store, explicitly not wired here (§9, §12). The math those objects carry
is already theorem-graded in `dn-temporal-retrieval-algebra` and test-pinned in `core/temporal/`.

## 9. Non-goals

- **No general capability-scope type system** (§2.1 bounded lattice) — `ReferenceView` ships as another
  *partial* scope instance (like the existing `OpsView`/`MirrorView`), built BEFORE the general algebra,
  exactly as the note says the Views are "partial instances." The §2.1 type system is a later graduation.
- **No wiring of `core/temporal`** (X_cite / operators) — turning the algebra's output into a query
  answer (β₁ threads, severed-citation curvature) is a distinct downstream plan (§12).
- **No build-time repo-derived twin** (§2.4) — this plan is the IN-CORE reader; the build-plane twin (so
  the orchestrator/builders can look up citations, findings 0059/0061's other customer) is a later plan.
- **No magnetic Laplacian** (`dn-magnetic-laplacian` — deferred behind gates), no alignment instrument
  (§2.6 second half — projects `K_sem` onto the structural spectral manifold; needs the embedding Gram),
  no diachronic interpreter (§2.7 → Track D charter).
- **No edit to `reference_edges.py` or `code_sensor.py`** — the store/extractor are reused as-is.

## 10. Stop-and-raise conditions

- The store read API can't answer "current citations" without a commit anchor that the ledger/HEAD
  doesn't supply (e.g. the daemon's projection commit ≠ HEAD in a way that makes the default wrong) →
  **file a `codebase` finding**, pin the anchor explicitly, do not guess "now."
- The repo-grep oracle disagrees with the store SO broadly (recall near zero) that the sensor is
  substantively broken (not just precision-gated) → **file a `codebase` finding** (the extractor, not
  this view, is the defect) and record the number; do not lower the floor to force green.
- Building `ReferenceView` reveals it cannot be read-only without importing a mutator surface → narrow,
  file a finding; never widen scope to `add_batch`.
- Any blessing flip → must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives | Re-entry |
|---|---|---|---|
| The "current" commit anchor | active run's `commit_sha` (`RunLedger.last()`), else git HEAD | union across ALL history (rejected: returns stale historical citations); `max(created_at)` commit (rejected: couples to write-time, not the running code) | if the daemon's projection commit and HEAD diverge in practice |
| `connected_set` includes self? | pin at build (recommend: exclude `ref` itself; return only reached others) | include self (rejected: noisy for the bookkeeping use) | — |
| A `store.latest_commit()` read helper | NOT added (the factory resolves the anchor from the ledger/HEAD, off the store) | add it to `reference_edges.py` (deferred: keeps this plan's write_scope off the store) | if a store-side "latest projected commit" is needed elsewhere |
| The φ_ref observation stream (§2.6 discipline 3) | NOT built (the oracle PRINTS the number; recording it as a self-sensing stream is future) | wire a `φ_ref` dual to `φ_self` now (deferred: needs the self-sensing projection seam) | when longitudinal sensor-fidelity tracking is wanted |

## 12. Dependency & ordering summary

Blast-radius order: **Item 1** (the read window) → **Item 2** (connected_set, builds on it) → **Item 3**
(the oracle, reads the window). All in `core/reference_view.py` + two test files → one session, not
parallel. Model opus/high (deterministic, read-only, settled design — no fable, no xhigh). `depends_on:
[]`.

**Downstream graduations this note still licenses (future plans, NOT this one):**
1. The **build-time repo-derived twin** (§2.4) — the same read surface for the orchestrator/builder plane
   (findings 0059/0061's other customer), rebuilt locally from the repo, never a sealed-store handle.
2. The **general capability-scope type system** (§2.1 bounded lattice) — retrofits `OpsView`/`MirrorView`/
   `ReferenceView`/`EffectView` as instances of one scope algebra. **Fable-grade design** (note §1.3
   item 2) — the one piece in this arc that may want fable when built.
3. **Wiring `core/temporal`** into a query answer (X_cite β₁ threads, `‖[d,τ]‖` citation-coherence over
   the live graph) — the algebra's first production consumer beyond tests.
4. The **alignment instrument** (§2.6) + the **diachronic interpreter** tiers (§2.7 → the Track D charter).

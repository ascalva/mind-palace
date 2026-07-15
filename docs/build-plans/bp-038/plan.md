---
type: build-plan
id: bp-038
alias: CQ-wire-2
status: proposed
design_ref:
  - docs/design-notes/core-query-protocol.md
  - docs/design-notes/temporal-retrieval-algebra.md
contract: builder
write_scope:
  - core/temporal_view.py
  - tests/unit/test_temporal_view.py
  - tests/integration/test_temporal_view_live.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 220k
    rationale: >-
      Read-only over a settled, test-pinned surface (`core/temporal/{operators,superconnection,
      boundary}.py` are built + graded), BUT heavier than bp-037: a real complex-restriction helper
      (`_restrict`), σ resolution across two snapshots with a genuine appear/disappear policy, and a
      second axis (the supersession poset over VersionStore). More design judgment per item than
      bp-037's pure wiring, so estimated above it. Self-driven lands ~0.5–0.8×. No fable (the math is
      banked theorem-grade in `dn-temporal-retrieval-algebra` §2.2–§2.3).
  actual: null
depends_on: [bp-037]
parallelizable_with: []
created: 2026-07-15
updated: 2026-07-15
links:
  - docs/design-notes/core-query-protocol.md
  - docs/design-notes/temporal-retrieval-algebra.md
  - docs/build-plans/bp-037/plan.md
  - core/temporal_view.py
  - core/temporal/operators.py
  - core/temporal/superconnection.py
  - core/temporal/boundary.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — `CQ-wire-2` (bp-038): two-snapshot `‖[d,τ]‖` citation-coherence + supersession health

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Graduated from ratified `dn-core-query-protocol` §2.5/§2.7 + `dn-temporal-retrieval-algebra` §2.2–§2.3,
and gated on **bp-037** (its `TemporalView` surface is now BUILT, so this plan extends a real interface,
never an inferred one). bp-037 wired the single-snapshot half (β₁ threads); this wires the **two-snapshot
half** — the citation-coherence obstruction `‖[d,τ]‖` (the count of citations that fail to carry forward
across a supersession boundary) plus the supersession poset's `δ_D²=0` well-foundedness.

**Read-only, in-core, no model** — same posture as bp-037. This adds no store *write* handle and no
model; it reads `ReferenceEdgeStore` (via two `TemporalView`s already assembled) and `VersionStore`.
Model tier **opus** — deterministic engineering over a settled, theorem-graded surface; **no fable**.

**The design question this plan settles (§3):** σ resolution across two commits — what "severed" means
when a note appears/disappears between snapshots. Ruling proposed here (owner ratifies at the gate):
**restrict to the common node set** (measure citations lost *between notes present at both commits*);
node addition/deletion is a separate, separately-reported axis.

## 1. Objective

Turn the built two-snapshot temporal operators into a live coherence read. `core/temporal/operators.py`
(`σ_*`, `sigma_node_map`, `t_active`), `superconnection.py` (`curvature`, `curvature_norm` = `‖[d,τ]‖`,
`severed_citations`, `is_flat`), and `boundary.py` (`supersession_poset`, `delta_D_squared_is_zero`)
are built + graded but **test-only**. Extend `TemporalView` with **`coherence_to(other: TemporalView)`**
— given two commit-anchored views, resolve σ, and report `‖[d,τ]‖` (severed-citation count), the severed
edges, `is_flat`, and the node/edge deltas — and add a **supersession well-foundedness** read
(`δ_D²=0` over the version chains). Prove both on the live graph (435 commits carry corpus→corpus
edges — data confirmed at bp-037 seal).

## 2. Context manifest

Read whole, in order:

1. `core/temporal_view.py` — the bp-037 surface being EXTENDED. `TemporalView` (frozen: `_complex:
   CitationComplex`, `commit`), `.over(store, *, commit)`, `open_temporal_view(config, *, commit)`.
   The view holds NO store handle — so two-snapshot work compares two already-assembled views
   (`coherence_to` accesses `self._complex`/`other._complex`, same-class private access).
2. `core/temporal/operators.py` — `sigma_node_map(cx_n, cx_np1, sigma: dict[str,str]) -> dict[int,int]`
   (`:31`; σ MUST be total on cx_n.nodes + INJECTIVE, else `DiamondError`/`ValueError`); `pushforward_0`
   (`:63`), `pushforward_1` (`:75`); `DiamondError` (`:25`). Linear-chain only.
3. `core/temporal/superconnection.py` — `severed_citations(cx_n, cx_np1, index_map) -> list[(int,int)]`
   (`:25`); `curvature_norm(...) -> int` (`:63`, `‖[d,τ]‖` = # severed, combinatorial v1);
   `is_flat(...) -> bool` (`:71`). The closed form: `[d,τ]` supported EXACTLY on severed citations.
4. `core/temporal/boundary.py` — `supersession_poset(version_store, doc_ids) -> SupersessionPoset`
   (`:114`, reads `VersionStore.history`); `delta_D_squared_is_zero(poset) -> bool` (`:166`);
   `SupersessionCycleError` (`:31`, a cycle is stop-and-raise). `poset_from_chains` (`:98`) for fixtures.
5. `core/temporal/complex.py` — `CitationComplex` (`:37`: `nodes`, `node_index`, `edges`, `A_cite`;
   `.n_nodes`/`.n_edges`); `build_citation_complex(store, *, commit)` (bp-037). The `_restrict` helper
   (§6) rebuilds a sub-complex over a node subset WITHOUT a store (re-index nodes, filter edges, rebuild
   `A_cite` binary) — mirrors `build_citation_complex`'s assembly (`:83`–`:92`).
6. `core/stores/versions.py` — `VersionStore.history(doc_id)` (`:121`), `count()` (`:165`),
   `open_version_store(config)` (`:177`). **`doc_id == source_path`** (bp-031, `:DDL comment`) — the
   SAME namespace as X_cite node ids (repo-relative doc paths), so poset docs cross-reference X_cite
   nodes directly (§3 Q3).
7. `docs/design-notes/temporal-retrieval-algebra.md` §2.2 (the σ operators theorem-grade), §2.3
   (Result 2: `‖[d,τ]‖` PROVEN = the severed count, not a proxy), §2.4 (the isolation invariant).
8. `docs/build-plans/bp-037/plan.md` — the sibling; its §11 parked "expose the harmonic threads"
   (still count-only) and the eager-assembly decision this plan inherits.

## 3. Investigation & grounding

- **Q1 — σ resolution across two commits (THE open design question) → restrict to the common node
  set.** `sigma_node_map` requires σ **total on cx_n.nodes** and **injective**. X_cite nodes are stable
  doc paths (bp-031 rename-carries-forward), so the natural σ is **identity**, but a note that stops
  being a citation endpoint between commits is in `X_n` and NOT `X_{n+1}` → identity is not total → a
  raise. **Ruling (owner ratifies):** `coherence_to` computes `common = X_n.nodes ∩ X_{n+1}.nodes`,
  **restricts `X_n` to a sub-complex over `common`** (via `_restrict`, §6), sets σ = identity on
  `common`, and measures severed citations there. Semantics: *"of the citations among notes present at
  BOTH commits, how many failed to carry forward."* The rejected alternative — **augment `X_{n+1}`** with
  the missing nodes as isolated vertices so σ is total on ALL of `X_n` (counting deletion-induced
  severing too) — is recorded in §11; it conflates "a citation was removed" with "a note left the
  graph," which node/edge deltas report separately and more honestly. `[grounds: operators.py:31-52
  totality/injectivity contract; superconnection.py:25-37 severed = image-not-an-edge.]`

- **Q2 — Where do two views come from, given the store-less frozen view?** bp-037's `TemporalView`
  holds `_complex` + `commit`, no store (deliberately). Two-snapshot coherence therefore compares TWO
  views: `TemporalView.over(store, commit=a).coherence_to(TemporalView.over(store, commit=b))`. The
  method reads only the two views' `_complex` fields (same-class private access) — no store handle is
  added to the frozen type, the read-only/no-leak invariant is preserved. A convenience factory
  `open_coherence(config, commit_a, commit_b)` opens the store once, builds both views, returns the
  report. `[grounds: temporal_view.py TemporalView is store-less by construction.]`

- **Q3 — The supersession poset's identity (does `δ_D²=0` cross-reference X_cite?) → YES, same
  namespace.** `VersionStore.doc_id == source_path` (bp-031, `versions.py` DDL comment) and X_cite node
  ids are repo-relative doc paths — the SAME identity. So `supersession_poset(version_store, doc_ids)`
  over `doc_ids = <the docs of interest>` is well-defined and its elements share identity with citation
  nodes. The poset δ_D²=0 check is a well-foundedness read on the version chains (28 rows live), a
  DIFFERENT axis from citation coherence (D-arrows vs F-edges — A5 keeps them separate). Exposed as its
  own read (`supersession_wellfounded`), never mixed into `A_cite`. `[grounds: versions.py:69-88.]`

- **Q4 — What IS a "snapshot," and is two-snapshot meaningful on the live store? → a COMMIT is a
  time-LABEL for a full re-projected citation graph; the meaningful unit is a DISTINCT snapshot.** The
  store holds one row per (edge, commit); the sensor re-projects the WHOLE corpus→corpus graph at each
  commit it runs on (not a delta), so `commit_sha` labels a full snapshot. **435 distinct commits** carry
  corpus→corpus edges — BUT the doc-citation stratum moves far slower than git commits tick, so
  consecutive commits are usually the SAME snapshot. Probed 2026-07-15: the **6 most-recent commits are
  ONE identical 217-pair snapshot** (they added doc files but no new which-note-cites-which); the graph
  only differs back at `02b121d` (212 pairs). **Consequence (the owner's multi-rate point):** comparing
  "HEAD vs git-parent" would compare two IDENTICAL snapshots → `‖[d,τ]‖ = 0` trivially. So the meaningful
  comparison is between two **distinct** citation snapshots (commits whose corpus→corpus edge-set
  differs), and the live test (Item 3) selects those, never naive git-adjacency. `[grounds: live probe
  2026-07-15; reference_edges.py:120 commit_sha = "the commit the reading landed at".]`

- **Q6 — Does this lock out generalization? → No; `coherence_to(other)` is anchor- and stratum-agnostic
  by construction (owner constraint 2026-07-15).** The API compares ANY two commit-anchored views —
  every generalization layers on top without a redesign: (a) *distinct snapshots vs git-adjacency* is a
  caller/test selection concern, not an API constraint; (b) *different strata at different rates* — a
  code-citation coherence is the SAME operators with `direction="code_to_code"` instead of
  `corpus_to_corpus` (the one generalization point is `build_citation_complex`'s hardcoded direction —
  a future kwarg, not a rewrite); (c) *longitudinal multi-rate tracking* is a future `φ_coh` stream over
  the distinct-snapshot SEQUENCE, consuming `coherence_to`; (d) *corpus-time vs git-time* is a selection
  layer that dedups identical snapshots above the API. This plan scopes to the **corpus (doc) citation
  stratum** deliberately (single-stratum, per the note's Mode-1 framing; A5 keeps strata unmixed) — NOT
  as a ceiling. Recorded as generalization affordances in §11.

- **Q5 — DiamondError on the linear-chain operators.** `sigma_node_map` raises `DiamondError` if σ
  merges two nodes onto one (non-injective). With σ = identity on distinct doc paths, injectivity holds
  by construction (distinct paths → distinct images) — so a `DiamondError` here signals a data defect
  (two docs collapsed to one path), a stop-and-raise (§10), never silently averaged. `[operators.py:44.]`

## 4. Reconciliation

- **`TemporalView` is EXTENDED, not corrected.** bp-037 shipped the single-snapshot reads; this adds a
  two-snapshot method + a supersession read. No existing bp-037 behavior changes — the falsifier is "an
  existing bp-037 TemporalView read returns a different value." The class docstring's "Single-snapshot
  (bp-037 scope) … `CQ-wire-2`, a follow-on that extends this surface" is fulfilled; update it to note
  the coherence read now exists (cross-reference-on-extension).
- **`dn-core-query-protocol` frontmatter stale** (`design-only`) — the same standing note-erratum bp-035
  and bp-037 already flag; this plan is a third consumer. The ratified note is immutable (A8); the
  orchestrator batches the erratum. **This plan edits no design note.**
- No code is corrected/replaced — purely additive over the built `core/temporal` operators.

## 5. Write scope

- `core/temporal_view.py` — extend `TemporalView` with `coherence_to(other) -> CoherenceReport`, a
  `CoherenceReport` dataclass, the `_restrict` sub-complex helper, a `supersession_wellfounded(...)`
  read, and the `open_coherence`/`open_supersession_wellfounded` factories.
- `tests/unit/test_temporal_view.py` — coherence over known two-snapshot fixtures (a severed citation,
  a flat/no-severing case, `_restrict` correctness, DiamondError on a collapsed-path fixture) + poset
  δ_D²=0 over version-chain fixtures + a cycle stop-and-raise.
- `tests/integration/test_temporal_view_live.py` — the live two-anchor coherence (`‖[d,τ]‖` ==
  `len(severed_citations)`, Result 2) + the live poset well-foundedness, both skip-with-reason when data
  is absent.

**Deliberately OUT of scope:** `core/temporal/{operators,superconnection,boundary,complex}.py` (the
built operators — REUSED unchanged; `_restrict` lives in `temporal_view.py`, not `complex.py`), the
weighted `(β,z)` retrieval curve (TA-a/parked), the homotopy-coherent diamond `τ_k` (TA-c/parked — a
diamond is a stop-and-raise here), the general scope type system (§2.1 — `CQ-scope`), every store, and
the denylist.

## 6. Interfaces pinned inline

```python
# core/temporal_view.py — EXTEND the bp-037 TemporalView.

from dataclasses import dataclass
from core.temporal.complex import CitationComplex, build_citation_complex
from core.temporal.operators import sigma_node_map
from core.temporal.superconnection import curvature_norm, is_flat, severed_citations

@dataclass(frozen=True)
class CoherenceReport:
    """The two-snapshot citation-coherence between an earlier view (n) and a later view (n+1),
    over the notes present at BOTH commits (§3 Q1 restrict-to-common)."""
    commit_from: str
    commit_to: str
    common_nodes: int          # |X_n.nodes ∩ X_{n+1}.nodes| — the domain the coherence is measured over
    coherence_norm: int        # ‖[d,τ]‖ = # citations among common nodes that failed to carry forward
    severed: tuple[tuple[str, str], ...]   # the severed citation pairs (by note id), deterministic
    is_flat: bool              # ‖[d,τ]‖ == 0 ⟺ every common-node citation carried forward (F1)
    nodes_added: int           # |X_{n+1}.nodes \ X_n.nodes| — the separate node-delta axis (§3 Q1)
    nodes_dropped: int         # |X_n.nodes \ X_{n+1}.nodes|

# a module helper (NOT a store touch): rebuild a sub-complex over a node subset.
def _restrict(cx: CitationComplex, keep: set[str]) -> CitationComplex:
    """A sub-complex over `keep ⊆ cx.nodes`: re-index the kept nodes (sorted), keep only edges with
    BOTH endpoints kept, rebuild the binary A_cite — mirrors build_citation_complex's assembly, no
    store. Deterministic."""
    ...

class TemporalView:   # ... bp-037 fields/reads unchanged ...
    def coherence_to(self, other: "TemporalView") -> CoherenceReport:
        """Two-snapshot ‖[d,τ]‖ from THIS view (earlier, X_n) to `other` (later, X_{n+1}). σ =
        identity on the common node set (§3 Q1); X_n restricted to common; severed = X_n edges whose
        image is not an X_{n+1} edge. Same-class access to other._complex — no store handle needed."""
        ...

def open_coherence(config=None, *, commit_from: str, commit_to: str) -> CoherenceReport:
    """Open the store once, build both anchored views, return the coherence report."""
    ...

def supersession_wellfounded(config=None, *, doc_ids: list[str] | None = None) -> bool:
    """δ_D²=0 over the version chains (boundary.supersession_poset + delta_D_squared_is_zero); a
    SupersessionCycleError propagates (a data defect, §10). doc_ids=None ⇒ all versioned docs."""
    ...

# REUSED unchanged: operators.sigma_node_map, superconnection.{curvature_norm,severed_citations,
#   is_flat}, boundary.{supersession_poset,delta_D_squared_is_zero}, versions.open_version_store.
```

## 7. Items

### Item 1 — `_restrict` + `coherence_to` + `CoherenceReport` (the two-snapshot citation coherence)
- **Objective:** the `‖[d,τ]‖` read: restrict `X_n` to the common node set, σ = identity, report the
  severed count/pairs, `is_flat`, and node deltas.
- **Files:** `core/temporal_view.py`, `tests/unit/test_temporal_view.py`.
- **Acceptance test:** fixture X_n = a→b, b→c, c→d, d→a (4-cycle at c1); X_{n+1} = a→b, b→c, c→d (the
  d→a citation severed at c2, all nodes present) → `coherence_to` reports `coherence_norm == 1`,
  `severed == (("a","d"),)` (or the canonical ordering), `is_flat is False`, `nodes_dropped == 0`. A
  no-severing fixture (X_{n+1} ⊇ X_n's edges) → `coherence_norm == 0`, `is_flat is True`. A dropped-node
  fixture (X_n has node e with an edge, absent in X_{n+1}) → e excluded from `common`, `nodes_dropped
  == 1`, and the e-edge NOT counted as severed (restrict-to-common semantics, §3 Q1). `_restrict` over a
  node subset yields the expected sub-complex (nodes/edges/A_cite).
- **Falsifier:** `coherence_norm != len(severed)` (Result 2 inversion broken); OR a dropped-node edge is
  miscounted as severed (augment semantics leaked in); OR `_restrict` keeps an edge with a dropped endpoint.
- **Invariant(s):** read-only; no store handle added to the frozen view; `A_cite`/`E_disp` never mixed
  (A5 — this touches only the citation backbone).  **Touches stored data?** No.  **Parallelizable?** No.

### Item 2 — `supersession_wellfounded` (the poset δ_D²=0 health)
- **Objective:** wire `boundary.supersession_poset` + `delta_D_squared_is_zero` over `VersionStore` into
  a read; a cycle raises `SupersessionCycleError` (stop-and-raise, never a silent false).
- **Files:** `core/temporal_view.py`, `tests/unit/test_temporal_view.py`.
- **Acceptance test:** over a version-chain fixture (`poset_from_chains({"docs/a.md":[1,2,3]})`)
  `supersession_wellfounded` returns True; a planted cycle fixture raises `SupersessionCycleError`; the
  factory resolves `doc_ids=None` to all versioned docs.
- **Falsifier:** a cyclic chain returns True instead of raising (H0 violation swallowed); OR the poset is
  built from citation edges instead of version chains (A5 — wrong store).
- **Invariant(s):** reads `VersionStore` only; `E_disp` (directed, acyclic) never symmetrized into
  `A_cite`.  **Touches stored data?** No.  **Depends on:** independent of Item 1 (different store/axis).

### Item 3 — the live two-anchor coherence + live poset health
- **Objective:** on the live store, select the two most-recent **DISTINCT** citation snapshots (§3 Q4 —
  skip commits whose corpus→corpus graph is identical to the newer one, so the comparison is not
  trivially empty), compute `open_coherence`, and assert `coherence_norm == len(severed)` (Result 2) on
  real data; run `supersession_wellfounded` over the live version chains and assert True (or a recorded
  honest raise). PRINT the coherence norm + node deltas + the two anchor commits.
- **Files:** `tests/integration/test_temporal_view_live.py`.
- **Acceptance test:** skip-with-reason if fewer than **two distinct** corpus→corpus snapshots exist
  (fresh worktree / a single snapshot); else pick the two most-recent distinct snapshots, assert the
  Result-2 inversion `coherence_norm == len(severed)` holds live, and print the numbers + both anchors.
  Does NOT assert a fixed `‖[d,τ]‖` VALUE (the corpus evolves) — only the inversion invariant + node
  deltas + well-foundedness. (A distinct-snapshot pair may still have `‖[d,τ]‖ = 0` if edges were only
  ADDED, none severed — that is honest: `is_flat=True`, `nodes_added>0`. The point is a real comparison.)
- **Falsifier:** `coherence_norm != len(severed)` live (a real assembly bug); OR the poset raises on the
  live chains (a rename-fork data defect — plan §10 → a codebase finding, NOT a swallowed False).
- **Invariant(s):** read-only over live stores; the oracle is the direct severed-count, never a proxy.
- **Touches stored data?** No.  **Depends on:** Items 1, 2.

## 8. Math carried explicitly

`‖[d,τ]‖` is the norm of the superconnection curvature `[d,τ]` for `𝔸 = d + τ` (τ = σ^*), supported
**exactly** on severed citations (edges of `X_n` whose σ-image is not an edge of `X_{n+1}`); Result 2
(`dn-temporal-retrieval-algebra` §2.3, PROVEN tight) makes it EQUAL the discrete severed count, so the
operator IS the invariant, not a proxy — the falsifier cross-checks the two. **Combinatorial v1** (each
severed citation weighs 1; the weighted `(β,z)` form is TA-a/parked). σ is the linear-chain
correspondence (single-valued, injective); a fork/merge diamond is a `DiamondError` stop-and-raise (TA-c
parked — never silently averaged). `δ_D²=0` is the order-complex cochain identity on the supersession
poset — zero **iff** the relation is a genuine strict partial order (acyclic, H0). The `_restrict`
sub-complex is a set restriction on nodes/edges + a rebuilt binary incidence — no spectral change. No
NEW math object; this wires theorem-graded ones. **A5 is load-bearing:** the undirected citation
backbone `A_cite` (`E_geom`) and the directed supersession arrows `E_disp` are NEVER unified into one
`L₁` — Item 1 touches only `A_cite`, Item 2 only the version poset.

## 9. Non-goals

- **No weighted retrieval / magnetic upgrade** (`(β,z)`, `L^{(q)}` — TA-a/parked).
- **No homotopy-coherent diamond `τ_k`** (TA-c/parked) — a fork/merge diamond is a stop-and-raise, not
  handled here.
- **No `π_active`/`t_active` active-view compression read** — that is the "current view" projection, a
  separable read (bp-037's `T=now` is already the default via the anchor); expose it only if a consumer
  needs it (§11).
- **No general scope type system** (§2.1 — `CQ-scope`), **no diachronic dreamer lens** (§2.7 — `DD-1`,
  gated on A7 + the lens contract; this View is what DD-1 will *consume*).
- **No store edits, no `core/temporal/**` edits** — the operators are reused as-is; `_restrict` is a
  view-local helper.

## 10. Stop-and-raise conditions

- σ cannot be made total/injective without an arbitrary choice beyond restrict-to-common (e.g. the live
  data has two docs collapsed to one path → `DiamondError`) → **file a `codebase` finding** (a data
  defect, likely a rename fork — `supersession-lifecycle` §7), do not silently average or drop.
- The live `‖[d,τ]‖` and the direct severed count disagree → **file a `codebase` finding** (Result 2
  broken — an assembly bug), record both; do not relax to an inequality.
- The live supersession poset raises `SupersessionCycleError` → **file a `codebase` finding** (a version
  chain forked — the bp-031 rename-stability gap), record it; do NOT swallow it into a False.
- Extending `TemporalView` reveals `coherence_to` needs a store handle on the frozen view → narrow (build
  both views outside, pass the second in), **file a finding**; never add a mutable store handle.
- Any blessing flip → must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives | Re-entry |
|---|---|---|---|
| σ across two snapshots (appear/disappear) | restrict to the common node set; node deltas reported separately (§3 Q1) | augment X_{n+1} with isolated vertices so σ is total on all X_n (rejected: conflates citation-removal with node-departure) | if a consumer needs deletion-induced severing counted as coherence loss |
| Which two anchors the live test compares | the two most-recent **DISTINCT** citation snapshots (§3 Q4) | HEAD vs git-parent (REJECTED: the 6 latest commits are one identical snapshot — a trivially-empty compare); a fixed pair (rejected: brittle); all-consecutive-pairs sweep (deferred: the φ_coh stream) | when longitudinal coherence tracking is wanted (a φ_coh stream) |
| Expose `π_active`/`t_active` (active-view compression) | NOT exposed (the anchor already gives `T=now`) | a `.active_view()` read returning the compressed cochain (deferred) | when a consumer needs the transported+compressed cochain, not just the norm |
| Weighted severed count (a severed high-potential citation weighs more) | combinatorial (each severed edge weighs 1) | potential-weighted `‖[d,τ]‖` (TA-a/parked — needs the weighted `A_cite`) | the metric-coherence tier (Result 4) is built |
| Which docs the poset covers | all versioned docs (`doc_ids=None`) | only X_cite nodes at an anchor (deferred: couples the two axes) | if a citation-scoped poset health is wanted |

**Generalization affordances (owner constraint 2026-07-15 — on record so nothing forecloses the
future).** `coherence_to(other)` is anchor- and stratum-agnostic; every generalization layers on the
same API without a redesign: (1) **per-stratum coherence** — a code→code / code→corpus coherence is the
same operators with a different `direction`; the ONLY change point is `build_citation_complex`'s
hardcoded `direction="corpus_to_corpus"` (a future kwarg, not a rewrite). (2) **longitudinal / multi-rate
tracking** — a `φ_coh` observation stream over the SEQUENCE of distinct snapshots (each stratum at its
own rate), consuming `coherence_to`. (3) **corpus-time vs git-time** — the commit is only a label; a
corpus-time index that dedups identical snapshots is a selection layer above the API. (4) **the σ policy**
(restrict-to-common) is a *default*, not a lock — the augment alternative is a swap-in if a consumer
needs deletion-induced severing. This plan's corpus-only, git-commit-anchored, combinatorial v1 is the
FIRST instance, deliberately narrow, never a ceiling.

## 12. Dependency & ordering summary

Blast-radius order: **Item 1** (citation coherence — the heart) ‖ **Item 2** (poset health — independent
axis, different store) → **Item 3** (live cross-check of both). Items 1 and 2 are independent (different
stores); Item 3 reads both. All in `core/temporal_view.py` + two test files → **one session.** Model
**opus** (deterministic, read-only, settled + theorem-graded surface — no fable, no xhigh). `depends_on:
[bp-037]` (extends its `TemporalView`).

**Downstream this completes/gates:**
- With bp-038, `core/temporal` is **fully wired** (single- + two-snapshot; complex, operators,
  superconnection, boundary all have a live consumer) — "complete the algebra" (owner roadmap #1) is done.
- **`DD-1` the diachronic dreamer** (§2.7) consumes this coherence surface + β₁ threads, gated on A7 +
  the lens contract — the next unit after `CQ-scope` (owner roadmap #2, a Fable session post-Jul-17).

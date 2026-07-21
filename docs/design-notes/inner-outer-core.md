---
type: design-note
id: dn-inner-outer-core
status: ratified            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-20
updated: 2026-07-20
links:
  - docs/brainstorms/inner-outer-core.md           # THE WARRANT — the 2026-07-18/19 owner brainstorm, the 2026-07-20 layout directive, and the two 2026-07-20 rulings (22:08Z v2 predicate; 22:55Z temporal-math splits)
  - docs/brainstorms/hypothetical-subspace.md      # the first concrete outer-ring consumer (grounded in §2.8; NOT designed here)
  - docs/findings/finding-0103.md                  # the outer ratchet (19 → 0) this note refines, never launders
  - tests/unit/test_core_self_containment.py       # the existing outer scanner — UNCHANGED by this note
  - ops/import_lint.py                             # NETWORK_MODULES, the audited ban set the predicate reuses (DRY)
  - docs/design-notes/agent-taxonomy.md            # "core-resident" refines to outer-core-resident; the computation agrees (§2.8)
  - docs/design-notes/capability-scope-algebra.md  # the algebra the inner ring is the code-side home of
  - docs/build-plans/bp-065/plan.md                # precedent: math→core, clean break, no alias wrappers; the math/acquisition split §2.6 re-instates
  - docs/build-plans/bp-067/plan.md                # precedent: the config split that made config.loader inner-eligible
supersedes: null
superseded_by: null
warrant: null
---

# Inner core / outer core — the two-ring refinement of core self-containment

> Composed at **fable** (`claude-fable-5`, 2026-07-20, session-39 dispatched design pass). Filed as
> `draft`; ratification is an owner-only hand edit. **Design only; the two builds this note
> licenses are §3's M0 plan and the §2.6b S1 split plan.** Every membership claim below is
> **computed, not asserted**: the fixed point was run over `core/**` at `97c245c` (135 modules;
> re-verified unchanged at `658e090`, a docs-only commit) with an AST scanner extended from
> `tests/unit/test_core_self_containment.py` (relative-import resolution + third-party
> classification + closure iteration). Re-run at build time; the numbers here are evidence, not
> the enforced artifact. **Re-cut twice the same day**: first to adopt the owner's predicate
> ruling (v2, the 2026-07-20T22:08Z capsule — the first draft `fde4326` computed the alternatives
> and left ONE ruling open); then to convert the temporal-math splits from parked to licensed
> (the 22:55Z capsule — the owner fired P8's re-entry at design time, §2.6b).

## 1. Purpose and scope

`core/` is heterogeneous: a pure mathematical/algebraic kernel, a boundary/invariant layer, and
administrative machinery. The owner decided (brainstorm capsules 2026-07-19 and 2026-07-20) to
split it into two rings, and fixed four pillars this note designs **within, not around**:

1. Membership is **mechanical**: inner core = the maximal import-closed subset of `core/**` over
   an admissible base — computed, never curated. The base is the decided formula {stdlib, pinned
   pure-math third-party (numpy/scipy), the inner ring itself} as sharpened by the owner's v2
   ruling (§2.1): two audited subtractions, zero per-module judgment.
2. **Two nested ratchets + a direction law**: a new inner-ring test born green; the existing outer
   ratchet **unchanged**, still counting 19 → 0 over ALL of `core/`; outer imports inner, never
   the reverse. Explicit no-laundering clause.
3. Rings run through **modules, not packages**.
4. The eventual repo structure **physically reflects** the separation (owner directive,
   2026-07-20) — target layout and migration path are first-class here (§2.7).

This note decides: the adopted membership predicate — v2, owner-ruled — and the recorded, rejected
alternatives (§2.1); the closure semantics (§2.3); the enforcement artifacts, test by test (§2.4);
what "inner" does and does not mean (§2.5); the disposition of finding-0103's four
strata-overlapping parked inversions under the ring lens (§2.6); the licensed **S1**
math↔persistence splits that bring the temporal mathematics into the ring (§2.6b, owner-ruled
22:55Z); the target directory layout and the migration sequence with the no-laundering clause
intact at every step (§2.7); and the grounding of the ring boundary against its first consumer
(§2.8).

**Out of scope:** the hypothetical-subspace design itself (it graduates separately after this
note reaches draft — its brainstorm's parked decision); any change to the outer ratchet test; any
relaxation of any finding-0103 obligation; the sibling packages (`eval`, `ops`, `scheduler`, …)
— they are machinery *outside* core and are untouched by ring vocabulary (§2.8, the three-zone
picture).

## 2. Principles / decision

### 2.1 The membership predicate — import-grain, two audited subtractions (v2, owner-ruled)

**Decision (adopted, owner ruling 2026-07-20T22:08Z):** the admissible base is

> **(stdlib ∖ `ops.import_lint.NETWORK_MODULES` ∖ {sqlite3}) ∪ {numpy, scipy}**,

under strict closure semantics (§2.3). Two subtractions, each forced or ruled, neither a
per-module judgment call:

1. **∖ NETWORK_MODULES (computed-forced).** The decided formula applied literally
   (base = stdlib ∪ {numpy, scipy}) produces an indefensible artifact:
   `core/models/ollama_client.py` (urllib — the loopback HTTP client) and `core/sealing.py`
   (socket) land INSIDE the inner ring, because `urllib` and `socket` are stdlib. An "inner
   core" containing the repo's only two network-capable core files (the audited
   `NETWORK_ALLOWLIST` of `ops/import_lint.py`) would poison the term on day one — the literal
   predicate computes to 59 strict members including `models/*`, `agent.py`, `sealing.py`,
   `ingest/embed.py`. The subtraction reuses the **already-audited** ban set (DRY: no new taste
   surface; one source of truth for "network-capable"), and makes **inner ⊆ network-incapable a
   theorem with an empty allowlist**.
2. **∖ {sqlite3} (owner-ruled).** With only the network subtraction (the first draft's "v1"),
   the ring computes to 51 members and **contains the sqlite store layer** — `sqlite3` is
   stdlib, and the store modules are import-austere. The owner ruled that out (2026-07-20,
   *"i do like v2 more"*), with the taste rationale recorded honestly: **the inner ring should
   BE the founding language — the algebra, the mathematics, the sacred boundaries — not the
   austere plumbing.** Persistence machinery, however dependency-clean, is machinery. The
   subtraction is one named stdlib module; membership remains computed, never curated — the
   lever moved is the predicate (a ratified design decision), not any module's assignment.

**The rejected wider alternative (v1) is recorded, not deleted:** base ∖ NETWORK_MODULES only;
51 strict / 68 lax at `dcf76b7`; the ring reads as "the self-contained, network-incapable
substrate," sqlite stores inside. Rejected because that region is austerity-defined, not
meaning-defined. **Re-entry (parked, P2):** a consumer someday needs the network-incapable
plumbing region *named* — e.g. a sealed-perimeter audit or a grant category wants "store code
that provably cannot egress" as a first-class label. It would return as a separate, derived
label or middle ring — **never** by re-widening `INNER`.

Scanner semantics (both rings, identical): absolute imports + resolved relative imports;
`TYPE_CHECKING` imports and lazy in-function imports **count** (the outer scanner already counts
them — e.g. `core/factory/factory.py`'s TYPE_CHECKING reach is among the 19; `ast.walk` sees
function bodies, so `core/complex/temporal.py`'s lazy `import duckdb` at `:153` counts).
Limitation stated honestly: string-based `importlib.import_module` calls are invisible to both
scanners — falsifier F8 below.

**Is import-closure sufficient, or must the ring forbid I/O / clock / env reads?** Decision:
**the predicate stays import-grain** — no call-level purity analysis. Rationale: (a) every
enforcement surface this repo trusts is import-structural (the outer ratchet, the import
firewall, the P1 boundary tooth) — call-grain analysis (`datetime.now` vs the `datetime` type,
`open`, `os.environ`) is a different, brittler machine with a large false-positive surface, and
nothing yet consumes the stronger guarantee; (b) the honest cost is named in §2.5: v2 inner
still does **not** mean call-grain effect-free. The full purity predicate is parked as **v3**
(P1) with falsifier F1 as its trigger.

### 2.2 The computed membership — evidence, with every surprise flagged

At `97c245c`, under the adopted v2 predicate: **29 strict members** (runtime-true semantics,
§2.3) of 135 core modules; 42 under lax (per-module) semantics. Full list in Appendix A.
Against the brainstorm's expected seed:

| Expected | Computed | Verdict |
|---|---|---|
| `core/scope.py` | IN | as expected — the algebra is inner |
| `core/agent_scope.py` | IN | as expected |
| `core/complex/*` | **SPLIT 5/11 files** | **surprise** — `balance, curvature, hodge, laplacian, support` (+ the already-thin `__init__`) are in; `spectral` (sknetwork via `core/typedshims/sknetwork.py`), `topology` (ripser), `temporal` (duckdb, lazy+TYPE_CHECKING), `blocks`/`cut` (closure via spectral), `build` (closure) are out. The spectral half of the reasoning complex is **not** inner. |
| `core/graph/composed.py` | lax-IN, strict-OUT | **surprise** — pure by its own imports (numpy only); excluded solely because `core/graph/__init__.py:19,30` re-exports `conductance`/`sigma_star`, whose closure reaches `spine` → eval + sqlite stores. Packaging-blocked, not import-blocked (§2.3). |
| recursion | **SPLIT** | `recursion.py` IN; **`recursion_ops.py` OUT — it imports `sqlite3` directly (`recursion_ops.py:53`)**: inline persistence in what reads as a vocabulary module. Revised from the seed; the licensed S1 split (§2.6b) promotes it. |
| split: `sigma_star` math vs `acquire_mirror_cut` | **CONFIRMED — and structurally necessary under v2** | the module imports `core.temporal.spine` at top level (`sigma_star.py:58`); spine is outer twice over — its eval reach (`spine.py:98`, one of the 19) AND its sqlite store closure (`spine.py:88-96` → catalog/chatlog/derived/edges/runledger + attestation.store). Under v2 the second exclusion is **permanent by design** (spine is acquisition machinery), so the bp-065-style split — math stays inner, spine-touching acquisition moves outward — is the only route in for the graph math. (The first draft, under v1, thought the spine inversion alone might suffice; v2 voids that.) |
| split: `dreaming/cluster` vs pipeline | **REVISED** | `cluster.py` is already clean (numpy-only). The blocker is packaging: `core/dreaming/__init__.py:13-25` pulls the full pipeline (`dreamer` → attestation → cryptography). No within-module split needed — a packaging remedy (§2.3/§2.7). |

**The four large surprises, stated plainly:**

1. **Import-austerity and "the math" are different rings — the owner had to pick.** Under the
   network-only subtraction the sqlite store layer (15 of 19 `core/stores/*` modules) *computes
   inner*: `sqlite3` is stdlib and the store modules import nothing beyond stdlib +
   `core.config` + `core.provenance`. That 51-member ring was mechanically sound and
   semantically wrong for the owner's telos. **The v2 ruling (∖ sqlite3) is a predicate
   amendment, not a curation** — one named module subtracted, membership still computed — and it
   sweeps 22 modules out of the first draft's ring: the 13 sqlite-importing store modules plus
   **9 non-store modules** that leave via closure or direct import (next surprise).
2. **The temporal-geometry mathematics is store-coupled, and v2 makes it visible.** The whole
   temporal family leaves with the stores: `temporal/boundary.py:25` → `stores.versions`,
   `temporal/complex.py:34` → `stores.reference_edges`, dragging `operators`,
   `superconnection`, and the package. Likewise `dreams_view` (`dreams_view.py:26` →
   `stores.derived`), `chat_events` (`chat_events.py:36-38` → three stores), and — sharper —
   **`integrator.py:32` and `recursion_ops.py:53` import `sqlite3` directly**, holding inline
   persistence rather than going through `stores/`. Shown this exclusion set, the owner ruled
   (2026-07-20T22:55Z): *"I would want the temporal math in the inner core"* — so the
   math/persistence splits for the temporal family and the integrator/recursion_ops pair are
   **licensed work, not an open question** (§2.6b; computed preview: +7 → a 36-member ring).
   The store-typed View vocabulary (`dreams_view`, `chat_events`) stays parked (P9).
3. **The literal predicate admits the network.** §2.1's first subtraction exists because the
   computation demanded it — `ollama_client`, `sealing`, `models/*`, `agent`, `ingest/embed`
   are inner under the un-sharpened formula.
4. **Packaging is load-bearing — "directory moves are cosmetic" is falsified.** 13 modules are
   lax-inner but strict-outer purely because an ancestor `__init__.py` drags in an impure
   sibling (list in Appendix A.2; among them `graph.composed`, `dreaming.{cluster,graph,rnd}`,
   `attestation.record`, `factory.{roles,tools}`, `verdict.taxonomy`). The 2026-07-19 capsule
   called repackaging "optional cosmetics"; under runtime-true semantics the physical layout
   *changes membership*. The owner's layout directive is therefore not aesthetic — it is the
   remedy for a computed defect.

Pleasing confirmations: `core/config/loader.py` is inner (bp-067's split vindicated);
`core/mirror.py` (MirrorView) is inner — the firewall *vocabulary* is pure even though the
machinery that wields it is not; `provenance`, `constitution`, `matching`, `selfcheck`,
`velocity_view`, the ingest text machinery (`amend`, `chunk`, `logseq`, `pipeline`, `verify`),
and the two file-backed stores (`rawstore` — content-addressed archive, `sourceset`) are all
inner. The dreamer, librarian, and curator all compute **outer** — the machinery/agents
intuition holds exactly where dn-agent-taxonomy predicted (§2.8).

### 2.3 Closure semantics: strict (runtime-true), and what the strict/lax gap measures

Two defensible dependency semantics exist. **Lax**: a module depends only on the modules it
names. **Strict**: importing `core.a.b` executes `core/a/__init__.py` (and `core/__init__.py`),
so a module also depends on every ancestor package of everything it imports.

**Decision: the inner ring is defined and enforced under STRICT semantics.** The ring's promise
— "importing an inner module pulls in only inner + admissible base" — must be true *at runtime*,
or it is not a guarantee, merely a reading. Lax membership is a diagnostic, not a ring.

Consequences, stated as invariants:

- **`core/__init__.py` must stay import-free** (today: a docstring, zero imports). This needs no
  new test: under strict semantics `core` is an ancestor of every module, so a single impure
  import there collapses the computed fixed point to near-empty and the equality test (§2.4)
  goes catastrophically red. Structural, not conventional.
- **The strict/lax gap (13 modules at `97c245c`) is the packaging debt**, and it is exactly what
  the physical migration (§2.7) pays off: in the end-state, inner modules live under a subtree
  whose `__init__`s are inner by construction, and strict ≡ lax over that subtree. The gap is a
  *measurable* progress gauge for the migration. **Falsifier (F3):** thinning the responsible
  ancestor `__init__` (or moving the module in M2) fails to promote a listed gap module — then
  the contamination was not packaging-only and the gap analysis was wrong.

### 2.4 Enforcement — the artifacts, test by test (structural-enforcement rule)

Two new files, delivered by the M0 plan (§3). No other enforcement machinery changes — S1
(§2.6b) moves code but adds no new test surface; its promotions land as `core/rings.py` diffs
that assertion B1 below forces.

**A. The ring map — `core/rings.py` (new, inner by construction).** A stdlib-only module
declaring `INNER: frozenset[str]` (module names, not paths — survives M2 renames as a mechanical
edit in the move commit), `MATH_3P: frozenset[str] = {"numpy", "scipy"}`, and
`PLUMBING_STDLIB: frozenset[str] = {"sqlite3"}` (the v2 subtraction, §2.1 — declared beside the
map so the predicate's owner-ruled parameter has exactly one home; the network subtraction stays
where it already lives, `ops.import_lint.NETWORK_MODULES`). The map is a *declaration forced to
match a computation* — it exists so that every membership change is a reviewable diff in exactly
one file, named in a plan's `write_scope` (scope-guard therefore makes every promotion/demotion
plan-visible with zero new machinery).

**B. The inner-ring test — `tests/unit/test_inner_ring.py` (new, BORN GREEN).**
Recomputes the strict-v2 fixed point over `core/**` at test time and asserts:

1. `test_inner_ring_is_the_computed_fixed_point` — **computed == declared**, both directions.
   A new inadmissible import in an inner module removes it from the computed set → red until the
   map change is made explicitly (a demotion, §below). A module that *becomes* pure (a packaging
   remedy or math split lands) enters the computed set → red until the map adds it —
   **promotions are forced to be explicit artifacts**, the excavation made visible. New modules
   are classified automatically: pure ⇒ the map must claim them; impure ⇒ outer by default, no
   action.
2. `test_outer_never_imported_by_inner` — the direction law, asserted explicitly per member with
   its own error message. Mathematically this is a corollary of (1) — an import-closed set
   cannot reach its complement — but the law gets its own named tooth so a scanner regression
   cannot silently retire it. **Falsifier (F4):** an inner→outer import with (1) green means the
   scanner lies; assertion (3) exists to catch that.
3. `test_scanner_sees_known_impurities` — the honesty guard, mirroring the outer test's pattern:
   asserts the computed exclusions include known-outer modules for their known reasons
   (`sealing` via socket, `stores.chatlog` via sqlite3, `stores.vectorstore` via pyarrow,
   `temporal.spine` via eval, `complex.spectral` via sknetwork) and that the computed set is
   non-trivially large. A scanner that stops parsing cannot fake a green ring.

The test imports `NETWORK_MODULES` from `ops.import_lint` (tests are machinery; the arrow is
allowed) and `INNER`/`MATH_3P`/`PLUMBING_STDLIB` from `core.rings`. The fixed-point computation
itself lives in the test module. **A deliberate, named DRY exception:** the outer scanner in
`test_core_self_containment.py` is *not* refactored into a shared helper — pillar 2 pins that
file unchanged, and two independent scanners cross-check each other (a bug in one cannot blind
both; the same redundant-sensor argument as its own `test_scanner_sees_the_known_violation_set`).
The audited constant is reused; the 20-line scanner is intentionally not.

**C. The outer ratchet — UNCHANGED.** `tests/unit/test_core_self_containment.py` keeps counting
19 → 0 over **all** of `core/` (its domain is `core.rglob("*.py")` — every file under `core/`
stays bound no matter which ring claims it or which directory M2 moves it to, so long as it
remains under `core/`).

**D. The no-laundering clause, mechanized.** Four bindings:

1. *Domain preservation:* no module leaves `core/**` under this program, ever. A sanctioned
   relocation of a violating module out of core (a legitimate finding-0103 remedy shape) is NOT
   this program: it requires its own owner-blessed plan whose acceptance names the ratchet count
   delta explicitly. The default reading of any count drop is inversion, never relocation.
2. *Move-neutrality:* every M2 migration commit asserts outer-count-before == outer-count-after.
   This is doubly held: structurally (only inner members ever move, and inner members carry zero
   sibling imports **by definition** — violations live exclusively in outer modules, which do
   not move) and by the plan's acceptance re-running the ratchet on both sides of the move.
3. *Ring assignment cannot redefine a violation:* membership is computed from imports; a
   violating module is outer *because* it violates — there is no assignment step a violation
   could hide in.
4. *Map monotonicity:* the inner map may shrink only via an explicit plan line-item (a named
   demotion with rationale). Enforced by process — the map's single-file diff plus scope-guard's
   requirement that a plan name `core/rings.py` — the same tier of enforcement as the outer
   ratchet's "count only decreases." **Falsifier (F5):** a demotion ships without a plan
   line-item naming it.

### 2.5 What "inner" means — and does not mean

Under v2 the inner ring is what the owner founded the idea on: **the math, the algebra, and the
sacred-boundary vocabulary — the founding language of the system.** The scope lattice
(`scope`, `agent_scope`), the pure spectral/graph/complex mathematics that survives the 3p test,
the Constitution frame, provenance, the View firewall vocabulary (`mirror`, `velocity_view`),
the ingest text projections, and the two file-backed content stores (`rawstore`, `sourceset`).
The inner ring is not an agent and not a service — it is the vocabulary agents are written in;
nobody grants you arithmetic.

Three properties, stated with their honest edges:

- **Network-incapability holds a fortiori.** v2 ⊂ v1, and v1 already made inner ⊆
  network-incapable a theorem with an empty allowlist. Note carefully what did *not* move: the
  **security perimeter is still core-wide** — `ops/import_lint.py` bans network imports across
  ALL of `core/**` regardless of ring, so shrinking the ring surrendered no guarantee. The ring
  is a meaning boundary, not the egress boundary.
- **The store plumbing is outer-core machinery — by ruling, and now aligned with roles.** The
  sqlite store layer sits in the outer ring beside the machinery that operates it. "Outer core"
  still means *core-resident*: the three-zone picture stands — **inner ring ⊂ core; outer ring
  = core ∖ inner; the siblings (`eval`, `ops`, `agents`, `scheduler`, `edge`, `config`) are not
  core at all** — and finding-0103's arrow (everything → core, never the reverse) is untouched.
- **v2 inner is still NOT call-grain effect-free.** Two members prove it by inspection:
  `core/stores/rawstore.py` performs disk I/O via `pathlib` (a content-addressed file archive —
  no sqlite, so it computes in), and `core/config/loader.py` reads the environment
  (`get_secret`'s env path) and TOML files. Nobody may build on "inner ⇒ pure function." The
  full call-grain purity predicate (forbid disk/env/clock *calls*, not just imports) is parked
  as **v3** (P1) with falsifier F1 as its trigger and a real candidate consumer named there
  (the hypothetical subspace's isolation argument).

If the owner ever wants a different ring, the lever is a predicate amendment to this note
(ratified, one line, recompute) — **never** a per-module exception; curation stays impossible by
construction.

### 2.6 The four parked strata-overlapping inversions, under the ring lens

finding-0103's 16 machinery reaches include four that PROGRESS (session-27 game plan, Track 3)
parked as strata-overlapping — they touch the View/strata seam and fold into Track 2
("coordinate, don't invert blind"): `core/sensing.py → ops.effects` (ObservedView),
`core/ops_view.py → {eval.drift, ops.ledger}`, `core/reference_view.py → ops.lifecycle.runs`,
`core/temporal/spine.py → eval.harness.store`. Does the split change their disposition?
**Sequencing: no — all four stay folded into Track 2.** But under v2 their relationship to the
inner ring inverts from the first draft's reading, in a way worth stating precisely:

1. **The four inversions now serve ONLY the outer ratchet — none grows the ring.** All four
   modules are store-coupled beyond their violations: spine imports five sqlite stores plus the
   attestation store (`spine.py:88-96`); sensing reads the sqlite observation stores
   (`sensing.py:58-60`); reference_view reads the sqlite reference-edge store
   (`reference_view.py:52`). Under v2 each remains outer **even after its inversion lands** —
   the computed promotion set of every one of the four is **empty**. The first draft's
   "spine-keystone" claim (one line blocking four-plus expected inner members) was a v1 artifact
   and is withdrawn: under v2, spine's sqlite closure excludes it permanently-by-design, so the
   graph math's route into the ring is the **bp-065-style math/acquisition split** (§2.2 table),
   not the spine inversion.
2. **This decoupling is a sequencing gift, not a loss.** Ring growth no longer waits on any of
   the 19→0 inversions — including the slowest, security-sensitive ones. The v2 map is
   near-stable at birth: no open inversion touches any of the 29 members' closures, so the M2
   stability gates (§2.7) are reachable almost immediately. The 19→0 program and the ring
   program run genuinely in parallel, coupled only by the shared no-laundering clause.
3. **Each inversion still acquires a ring-lens obligation.** Its plan states the expected map
   delta up front (under v2: expected ∅ — ground-before-building applied to ring expectations;
   a surprise nonempty delta is falsifier F9 and files a finding), its target-state is "born
   outer-clean" (violation-free, computed at seal), and the laundering guard binds explicitly:
   relocating `sensing.py`/`ops_view.py` into `ops/` to dodge the ratchet is clause §2.4-D1 —
   an out-of-core relocation is its own owner-blessed decision with the count delta named,
   never a side effect of a Track-2 build.

**What grows the ring under v2, then:** (a) **packaging remedies** — the 13 gap modules
(Appendix A.2), promoted by thinning the responsible `__init__`s or by the M2 moves; (b) **math
extractions** — bp-065-shaped splits. Of these, the temporal/integrator set is **licensed by
this note** (§2.6b, owner-ruled); the sigma_star/conductance split (math inner, spine-touching
acquisition outward) remains named-but-not-yet-licensed — it is entangled with the graph
`__init__` packaging remedy and Track-2 coordination, and graduates separately.

### 2.6b The S1 split plan — the temporal math enters the ring (owner-ruled, LICENSED)

**The ruling (2026-07-20T22:55Z, capsule at `658e090`):** shown that v2-as-computed excludes the
temporal-mathematics family and the integrator/recursion_ops pair, the owner: *"I would want the
temporal math in the inner core."* That is the former P8 park's re-entry condition firing at
design time, pre-ratification — so this note converts it from parked to a **second licensed,
session-sized plan (S1)** beside M0. Shape pinned to precedent (bp-065 / the sigma_star pattern):
**the pure builder takes data; the store-reading acquisition seam moves one ring outward — the
machinery calls core, core returns data.** No behavior change; no new mathematics.

**Grounding (verified in code — the seams are thin):**

- `core/temporal/boundary.py` is **half-split already**: the pure, store-free core
  (`poset_from_chains`, `:98` — "the pure, store-free core `supersession_poset` delegates to")
  exists; the only store touch is the thin `supersession_poset(version_store, …)` wrapper at
  `:114-115` reading `VersionStore.history`. The split is relocating one wrapper.
- `core/temporal/complex.py`'s seam is **one function**: `build_citation_complex(ref_store, …)`
  at `:59` (the flag-complex math already delegates to inner `core/complex/hodge`).
- `core/integrator.py` holds a raw `ledger: sqlite3.Connection` dataclass field at `:136`
  beside pure gauge math, plus the two store-type imports (`:38-39`).
- `core/recursion_ops.py` has the inline `import sqlite3` at `:53` **and** — found at grounding,
  beyond the capsule's description — a `core.stores.derived` import at `:62`; the seam includes
  both.

**Computed promotion preview (simulated at `658e090` — the four files shedding exactly their
sqlite/store seams; the computation rules, not the estimate):** the ring becomes **36 strict /
49 lax; the packaging-debt gap stays 13**. Promoted, exactly the expected seven:
`core.integrator`, `core.recursion_ops`, `core.temporal` (pkg), `core.temporal.boundary`,
`core.temporal.complex`, `core.temporal.operators`, `core.temporal.superconnection`. No hidden
couplings surfaced — no named module remains excluded in the simulation.

**The plan sketch (mint at graduation, not here):** write_scope = the four core files + the new
outward seam home(s) + `core/rings.py` (+ tests). Acceptance is **mechanical**: the seven named
modules enter the computed fixed point and the equality test (§2.4-B1) forces each promotion as
a `core/rings.py` diff; the full local CI gate green; zero behavior change (the relocated seams
produce identical data — bp-065's P4 no-silent-change discipline). **§2-manifest DRY
obligation:** before minting any new persistence module for the integrator/recursion_ops inline
sqlite, audit whether an existing `core/stores/*` module already covers it (the owner's
reuse-before-reimplement rule; two of these files holding hand-rolled sqlite beside a 15-module
store layer is itself a smell S1 should resolve, not replicate). **The outer ratchet is
untouched:** every import moved is core-internal (`core → core.stores`), none is among the 19 —
the 19→0 program neither gates nor is gated by S1. **Sequencing: strictly after M0** — M0 lands
the born-green 29-ring as-is; S1 is the first promotion wave, and its map diff is exactly the
+7. **Falsifier (F10):** S1 lands and a named module still fails to enter the computed set ⇒ a
coupling exists beyond the audited seams; stop, file the finding, re-ground.

**What stays parked (P9): the store-typed View vocabulary.** `chat_events` and `dreams_view`
are each computed **exactly one hop out** — their sole inadmissible dependencies are store
imports (`chat_events` → `stores.chat_events` + `stores.chatlog`; `dreams_view` →
`stores.derived` for the `DREAM`/`FINDING` kind-constants and the `Artifact` type). They are
NOT trivially includable: unlike the S1 seams (acquisition calls that relocate), these imports
are **load-bearing types and constants in the modules' signatures** — bringing them in means
relocating shared types/constants inward or a typed-protocol seam, which is a design question
interacting with the TYPE_CHECKING stance (P6), not a mechanical wrapper move. Parked with that
shape named, re-entry at P9.

### 2.7 The physical end-state and the migration path (owner directive, first-class)

**Target layout — decision: one-sided `core/kernel/`.** The inner ring physically lives at
`core/kernel/**`, preserving relative subpaths (`core/scope.py → core/kernel/scope.py`;
`core/complex/laplacian.py → core/kernel/complex/laplacian.py`; `core/stores/rawstore.py →
core/kernel/stores/rawstore.py`). The outer ring **stays where it is** — outer is the
complement, `core/**` minus `core/kernel/**`. Rationale: (a) one migration direction, half the
churn — no mass `core/machinery/` move that would touch every outer file for zero enforcement
gain; (b) the separation is fully visible (the kernel subtree *is* the inner ring); (c) the
end-state test becomes self-describing — computed == everything-under-kernel; (d) "kernel" over
"inner" as the directory name because it is a noun that reads in import paths
(`core.kernel.scope`) and matches the owner's founding language; "inner/outer" remain the ring
names in prose. Packages the ring runs through (stores, complex, ingest, and post-remedy
graph/dreaming) will have two physical homes (`core/kernel/stores/` holding `rawstore`/
`sourceset` beside an outer `core/stores/` holding the sqlite layer) — that is the honest
physicalization of pillar 3, not an accident to hide. Under v2 the kernel tree is small and
sharply meaningful: the founding language, physically one subtree. Rejected: permanent re-export
facades to preserve old paths (`core/scope.py` shimming `core.kernel.scope`) — the owner's
no-alias-wrappers rule and bp-065's clean-break precedent; every move repoints all importers
repo-wide in the same commit.

**Migration sequence — four stages, enforcement stated at each:**

- **M0 — enforce the rings in place (the FIRST of the two licensed plans; no file moves).**
  `core/rings.py` + `tests/unit/test_inner_ring.py`, exactly §2.4 — unchanged in shape by
  either ruling, just a smaller map (29 at `97c245c`). Born green: the map is the fixed point
  recomputed at the build's HEAD (not this note's list — **falsifier F6:** if the M0 test lands
  red, the map was computed at a stale tree; recompute, never hand-edit toward green). Write
  scope: those two files, nothing else. Blast radius: purely additive. Sequencing: rides behind
  the lead build — this program does **not** preempt the diamond (brainstorm pin: bp-069
  remains the lead).
- **M1 — membership grows as remedies land.** The first vehicle is **S1** (§2.6b, the SECOND
  licensed plan, strictly after M0): the temporal/integrator splits, map +7 → 36. Thereafter:
  packaging remedies and further math extractions (§2.6) as riders on whichever plan lands
  them, never the finding-0103 inversions (their expected map delta is ∅); every such plan
  carries its ring-map delta because the equality test forces it, and `core/rings.py` joins its
  write_scope. The outer ratchet falls 19 → 0 on its own, fully parallel track; the inner map
  only grows (§2.4-D4). Enforcement: both tests, plus scope-guard making every promotion
  plan-visible.
- **M2 — physical migration, per-wave plans, entry-gated.** Begins only after ratification of
  this note AND per-wave stability: a wave may move when its membership has been stable across
  ≥ 2 sealed plans and no open plan names any module in the wave's closure. Waves must be
  import-closed against kernel-so-far (a wave's members' closures lie within kernel ∪ wave —
  no dangling inner-outside-kernel imports mid-migration). Suggested shape under v2 (exact
  manifests are computed at graduation, not pinned here — split at graduation, never
  mid-build): **K1** — the born-29, likely as one or at most two plans (the algebra and scope
  vocabulary; the complex math five; `provenance`/`constitution`/`mirror`/`matching`/
  `selfcheck`/`velocity_view`; `config.loader`; the ingest text machinery; `rawstore`/
  `sourceset`); **K2** — the packaging-debt promotions as their remedies land (the 13:
  `dreaming.cluster`, `graph.composed`, `attestation.record`, …), each moving in a later small
  commit; **K3** — the math-extraction promotions (the S1 seven — §2.6b, licensed, likely the
  first K-wave after K1 given S1's early sequencing; the graph math post-split, named but not
  yet licensed). Each move
  commit: `git mv` + repo-wide repoint + map rename + **outer count unchanged** (§2.4-D2) +
  inner test green + the full local CI gate. The outer ratchet reaching 0 is **not** a
  precondition for M2 — move-neutrality is structural (only violation-free modules move) — it
  is only a precondition for M3. Under v2 this decoupling is total (§2.6.2): the kernel can be
  physically real while the slowest inversion is still open, every step laundering-proof.
- **M3 — the flip.** When map == kernel-tree and the outer ratchet is 0: the test's declared
  side switches from `core/rings.py` to the tree itself (the map becomes derived or retires),
  and the program is complete. End-state statement: `core/kernel/**` is the inner core,
  self-verifying under strict semantics (strict ≡ lax over the kernel subtree — the packaging
  debt of §2.3 is provably zero); `core/**` minus kernel is the outer core; the outer ratchet
  stands green as the permanent perimeter.

### 2.8 Grounding the boundary — the first consumer, and the taxonomy

**The hypothetical subspace** (its brainstorm; NOT designed here) decomposes cleanly on the
computed boundary, which is the grounding pillar 4 asked for — and under v2 the decomposition is
*cleaner* than the first draft's:

- *Machinery (outer ring, or not core at all):* the TTL sweep and dispatch (scheduler-side — a
  sibling, outside ring vocabulary entirely); the dispatched dreaming agent
  (`core/dreaming/dreamer.py` — computed outer, closure via attestation); and the staging store
  — sqlite-backed staging now **computes outer** under v2, so the rings and the roles agree
  (the first draft had to explain away an inner-computing store; the ruling dissolved that
  wrinkle — machinery is outer both by role and by computation).
- *Mathematics (inner ring, some of it pending):* the graph ∪ subspace assembly is
  `core/graph/composed.py` — inner-target, today packaging-blocked (§2.2), promoted by the
  graph `__init__` remedy or the K2 move; σ*/conductance enter via the K3 math-extraction split
  (§2.6 — not via the spine inversion). **One honest flag for the subspace design pass:** the
  influence metric's *spectral* half (`core/complex/spectral.py`) is outer (sknetwork) and will
  not enter the ring without a dependency decision that is out of this note's scope (parked,
  P8) — the subspace note should treat instrument purity per-instrument, not assume "the
  instruments are inner."
- *Isolation:* a View-firewall variant for hypothetical reads is inner-eligible vocabulary —
  `core/mirror.py` (computed inner) is the precedent shape. If the subspace's isolation
  argument ever needs "provably effect-free," that is v3's re-entry (P1), named there.

**The taxonomy tie:** dn-agent-taxonomy's "core-resident" refines to **outer-core-resident**,
and the computation *agrees* rather than stipulates: the dreamer, librarian, and curator all
compute outer; the algebra they are clients of (`scope`, `agent_scope`) computes inner. The
inner core is not an agent — it is the vocabulary agents are written in. The data-side symmetry
stands: 𝔇 ungrantable at the center with grantable strata around it; the code side now has the
same geometry, with `CONSTITUTION.md` to data what the inner ring is to machinery: the fixed
points.

## 3. Consequences

- **Licenses exactly two build plans now, each session-sized:** **M0** (`core/rings.py` +
  `tests/unit/test_inner_ring.py` — additive-only, born green, no store or behavior change;
  acceptance and falsifiers are §2.4/§2.7-M0 verbatim; the plan recomputes the membership at
  its HEAD and treats Appendix A as expectation, not authority) and **S1** (§2.6b — the
  temporal/integrator math↔persistence splits, strictly after M0; acceptance mechanical: the
  seven named modules enter the computed fixed point, map diff +7 → 36; zero behavior change;
  the outer ratchet untouched).
- **Amends the working shape of future core plans (M1 riders):** any plan that lands a
  packaging remedy or math extraction adds `core/rings.py` to write_scope and states its
  expected promotion set in §3-grounding; finding-0103 inversion plans state their expected map
  delta (under v2: ∅) so a surprise is a finding, not a silent drift. No plan re-blessing
  needed for already-sealed work; this binds plans minted after ratification.
- **Licenses the M2 wave plans and the M3 flip** upon ratification + the §2.7 entry gates; each
  wave graduates as its own small plan with computed manifests.
- **Feeds the book:** the two-ring geometry, the v2 ruling (a predicate choosing *meaning* over
  *austerity*, mechanically), and the "excavation, not stain-removal" reframe of the
  finding-0103 program is a chapter-arc candidate once M1 shows motion (scribe debt, not now).
- **Does not** change the outer ratchet, the deploy-gate policy (finding-0105 decision-A
  deselection is unaffected — the inner test is green and never deselected), `MIRROR_READABLE`,
  the denylist 𝔇, the core-wide import firewall (§2.5 — the egress perimeter stays core-wide),
  or any sibling package.

## Parked decisions

| # | Decision | Default recorded | Re-entry condition |
|---|---|---|---|
| P1 | **v3** call-grain purity predicate (forbid disk/env/clock *calls* — `rawstore`'s pathlib writes, `config.loader`'s env reads, `datetime.now`) | NO — the predicate stays import-grain (§2.1) | falsifier F1 fires (a consumer relied on inner ⇒ effect-free and was burned), or a grant category needs "provably effect-free" (candidate: the hypothetical subspace's isolation argument, §2.8) |
| P2 | re-widening toward **v1** (the 51-member network-incapable ring, sqlite stores inside) | NO — v1 is the recorded-and-rejected wider alternative (§2.1) | a consumer needs the austere-plumbing/network-incapable region *named* (e.g. a sealed-perimeter audit label); returns as a separate middle ring or derived label, never by re-widening `INNER` |
| P3 | two-sided layout (`core/machinery/` for outer) | one-sided `core/kernel/` only | recurring misplacement/confusion in review during M2 (the two-home packages prove costly in practice) |
| P4 | extract the fixed-point computation from the test into `ops/` | computation lives in `tests/unit/test_inner_ring.py` | a second consumer materializes (statusline gauge, M2 tooling) |
| P5 | per-module `# ring:` header annotations | none — `core/rings.py` is the single declaration | reviewers repeatedly lack ring context at the file level |
| P6 | type-only (`TYPE_CHECKING`) import exemption for the inner ring | counted, same as the outer scanner | a genuine type-only inner need arises AND the laundering risk is argued down in a design pass |
| P7 | "librarian" = curator vs retrieval-serving agent (carried from the brainstorm) | vocabulary only; computed outer either way | its own design pass |
| P8 | `sknetwork`/`ripser` dependency decisions for the spectral/topology math (**amended 22:55Z:** the temporal/integrator splits this row once bundled were RULED and graduated to licensed work — §2.6b/S1; only the 3p-dependency half remains parked) | outer under v2; no shim work licensed | the subspace or instrument program needs the spectral math inside the ring |
| P9 | store-typed View vocabulary (`chat_events`, `dreams_view`) — computed exactly one hop out; their store imports are load-bearing types/constants, not relocatable acquisition seams (§2.6b) | outer; no type-relocation or protocol seam licensed | the S1 seal proves the split pattern and a follow-on wants these two; or a consumer needs the View vocabulary inner; interacts with P6's TYPE_CHECKING stance — decide there first |

## Falsifiers (the load-bearing set, collected)

- **F1** (§2.1/§2.5) — import-grain sufficiency: a consumer builds on "inner ⇒ effect-free" and
  a disk/env/clock effect under an inner label breaks a real guarantee ⇒ activate P1 (v3).
- **F2** (§2.1) — the v2 narrowing: a consumer needs, and cannot get, a trusted label for the
  excluded network-incapable plumbing (the sqlite store layer) ⇒ activate P2 — as a new label,
  never by re-widening.
- **F3** (§2.3) — packaging-debt claim: thinning the named ancestor `__init__` fails to promote
  a gap-listed module ⇒ the contamination was not packaging-only.
- **F4** (§2.4) — scanner honesty: an inner→outer import observed with the equality test green
  ⇒ the scanner lies; the known-impurities guard must be extended.
- **F5** (§2.4) — map monotonicity: a demotion ships without an explicit plan line-item.
- **F6** (§2.7) — born-green: M0's test lands red ⇒ stale membership computation; recompute at
  HEAD, never hand-edit the map toward green.
- **F7** (§2.4-D2) — move-neutrality: any M2 commit where the outer ratchet count changes.
- **F8** (§2.1) — scanner blind spot: a string-based dynamic import (`importlib.import_module`)
  smuggles an inadmissible dependency into an inner module. Both scanners share this limit; if
  observed, the scanner grows a `Call`-node check for `importlib` in inner members.
- **F9** (§2.6) — inversion/ring decoupling: a finding-0103 **inversion** plan lands with a
  nonempty ring-map delta (expected ∅ under v2) ⇒ the decoupling claim was wrong; file the
  finding and re-ground §2.6. (The licensed S1 split plan is NOT an inversion — its nonempty
  delta, +7, is its acceptance criterion, not this falsifier's trigger.)
- **F10** (§2.6b) — the S1 seam audit: S1 lands and one of the seven named modules still fails
  to enter the computed fixed point ⇒ a coupling exists beyond the audited store/sqlite seams;
  stop, file the finding, re-ground before forcing it.

## Appendix A — the computed membership at `97c245c` (v2 predicate, adopted)

### A.1 Inner ring, strict semantics — 29 of 135

```
core                                    core.ingest.logseq
core.agent_scope                        core.ingest.pipeline
core.complex                            core.ingest.verify
core.complex.balance                    core.matching
core.complex.curvature                  core.mirror
core.complex.hodge                      core.provenance
core.complex.laplacian                  core.recursion
core.complex.support                    core.scope
core.complex_types                      core.selfcheck
core.config                             core.stores
core.config.loader                      core.stores.rawstore
core.constitution                       core.stores.sourceset
core.ingest                             core.typedshims
core.ingest.amend                       core.velocity_view
core.ingest.chunk
```

(Lax semantics: 42 members — the 29 above plus the 13-module packaging debt of A.2. **Post-S1
preview**, simulated at `658e090`: 36 strict / 49 lax, gap unchanged at 13 — the 29 above plus
`integrator`, `recursion_ops`, `temporal`, `temporal.boundary`, `temporal.complex`,
`temporal.operators`, `temporal.superconnection`. A.1 remains M0's expectation; the +7 is S1's.)

### A.2 Packaging debt — lax-inner, strict-outer (13): promoted by `__init__` thinning or M2

`attestation.record` (via `core/attestation/__init__` → crypto → cryptography);
`dreaming.cluster`, `dreaming.graph`, `dreaming.rnd` (via `core/dreaming/__init__` → dreamer →
attestation); `factory.roles`, `factory.tools` (via `core/factory/__init__` →
`factory.factory`, a sibling violation); `graph.composed` (via `core/graph/__init__` →
sigma_star/conductance → spine); `models.registry` (via `core/models/__init__` →
ollama_client); `research.airlock`, `research.criteria` (via `core/research/__init__` → rank →
vectorstore); `sandbox.policy`, `sandbox.spec` (via runner → wasmtime); `verdict.taxonomy`
(via `core/verdict/__init__` → payload → attestation).

### A.3 Notable exclusions and their computed reasons

| Module(s) | Reason |
|---|---|
| the sqlite store layer — 13 modules (`chatlog`, `derived`, `edges`, `runledger`, `catalog`, `causal_edges`, `chat_events`, `agent_observations`, `authored_supersession`, `code_observations`, `observation_history`, `reference_edges`, `versions`) | **the owner's v2 ruling** (∖ sqlite3, 2026-07-20T22:08Z) — import-austere but plumbing, excluded by predicate, not by a computation change; they computed inner under the rejected v1 |
| `integrator`, `recursion_ops` | direct `import sqlite3` (`integrator.py:32`, `recursion_ops.py:53`; recursion_ops also `stores.derived` at `:62`) — inline persistence; **promoted by the licensed S1 split (§2.6b)** |
| `temporal.{boundary,complex,operators,superconnection}` + the `temporal` pkg | closure through the sqlite stores (`boundary.py:25`, `complex.py:34`) — the store-coupled math of §2.2 surprise 2; **promoted by the licensed S1 split (§2.6b)** |
| `chat_events`, `dreams_view` | store-typed vocabulary, exactly one hop out (`chat_events.py:36-38`, `dreams_view.py:26`) — load-bearing type/constant imports, not relocatable seams; parked (P9) |
| `sealing`, `models.ollama_client` | network stdlib (socket / urllib) — the two `NETWORK_ALLOWLIST` files, outer by the first subtraction |
| `models.*`, `agent`, `ingest.embed` | closure via `ollama_client` |
| `attestation.crypto`, `attestation.verify` | cryptography (pinned, not pure-math) |
| `complex.spectral`, `complex.topology`, `complex.temporal` | sknetwork / ripser / duckdb (lazy + TYPE_CHECKING both counted) |
| `stores.vectorstore`, `stores.telemetry`, `stores.curated_store`, `stores.verdicts` | pyarrow / duckdb / closure via vectorstore / closure via `verdict.payload` → attestation |
| `sandbox.runner`, `ingest.watch`, `typedshims.{lancedb,psutil,sknetwork}` | wasmtime / watchdog / shimmed 3p |
| `shadow`, `effect_proposal`, `factory.factory`, `interface`, `ops_view`, `reference_view`, `sensing`, `spine` | the 19 sibling violations (finding-0103) — the 8 violating files; all four §2.6 modules ALSO store-coupled, so outer under v2 even post-inversion |
| `graph.*`, `temporal.atlas` | closure via `spine` (eval + sqlite stores) |
| `dreaming.*`, `curator`, `librarian`, `verdict.*`, `runtime`, `vitals`, `research.*`, `temporal_view` | closure via the above |

Calibration — counts under the three predicates, strict/lax: decided-literal 59/75 (admits the
network client); v1 network-only subtraction 51/68 (recorded-and-rejected, P2); **v2 adopted
29/42**, becoming **36/49 after the licensed S1 splits** (§2.6b preview). Delta v1 → v2: 22
modules leave (13 sqlite stores + 9 via closure or direct sqlite3), 0 enter; S1 recovers 7 of
the 9 non-store leavers (all but the P9 pair).

## Cross-references

`docs/brainstorms/inner-outer-core.md` (all four capsules — the warrant; the v2 ruling at
2026-07-20T22:08Z, commit `97c245c`; the temporal-math ruling at 22:55Z, commit `658e090`) ·
`docs/brainstorms/hypothetical-subspace.md` (§2.8 grounding) · `docs/findings/finding-0103.md`
+ `tests/unit/test_core_self_containment.py@97c245c` (the outer ratchet, 19 at authoring) ·
`ops/import_lint.py` (`NETWORK_MODULES`, `NETWORK_ALLOWLIST`) ·
`core/temporal/spine.py:88-96,98` (the store closure + the eval reach) ·
`core/graph/sigma_star.py:58` + `core/graph/__init__.py:19,30` (the packaging block) ·
`core/dreaming/__init__.py:13-25` · `core/attestation/__init__.py:8-21` ·
`core/complex/temporal.py:26,153` (lazy import counted) · the S1 seams (§2.6b):
`core/temporal/boundary.py:98,114-115` (pure poset core + the one VersionStore wrapper) +
`core/temporal/complex.py:59` (`build_citation_complex`) + `core/integrator.py:32,38-39,136`
(inline sqlite3 + store types + the `Connection` field) + `core/recursion_ops.py:53,62`
(inline sqlite3 + `stores.derived`) · `core/dreams_view.py:26` + `core/chat_events.py:36-38`
(the P9 store-typed pair) · `core/sensing.py:58-60` + `core/reference_view.py:52` (the §2.6
store couplings) · `docs/design-notes/agent-taxonomy.md` §2.1 (residence column) ·
`docs/design-notes/capability-scope-algebra.md` (the algebra housed in the ring) ·
`docs/build-plans/bp-065/plan.md` (clean break + the math/acquisition split precedent) ·
`docs/build-plans/bp-067/plan.md` (the config split that made `config.loader` inner-eligible) ·
`docs/PROGRESS.md` session-27 (the Track-2/Track-3 game plan the §2.6 dispositions slot into).

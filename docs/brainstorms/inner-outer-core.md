# Brainstorm — inner core / outer core: the two-ring refinement of core self-containment

> Captured by the orchestrator from a live owner brainstorm (2026-07-18 evening local, fable
> session-29). Owner's seed, verbatim: *"inner core vs outer core, it feels like the core is serving
> a lot of purposes, like we now have more administrative tasks like retrieval, writes, updates,
> store access, config injection … the inner core is what holds the math, what holds sacred
> boundaries, the query language/algebra, the dreamer and the librarian could be considered outer
> core agents."* Candidate to graduate into `dn-inner-outer-core` at the next design pass.

## 2026-07-19 UTC (session-29)

### The idea

`core/` is heterogeneous: a pure mathematical/algebraic kernel (the scope lattice, the spectral
family, the graph math, result typing), a boundary/invariant layer (provenance, View firewalls), and
an administrative machinery layer (stores, retrieval, ingest, config injection, the dreamer's
operational pipeline). Split it into two rings: **inner core** (the math, the sacred boundaries, the
query language/algebra) and **outer core** (machinery + core-resident agents — the dreamer, the
librarian/curator).

### The scrutiny pass — what makes this real rather than taxonomy

**The ratchet has been announcing this split empirically.** The self-containment ratchet's remaining
19 reaches live at the machinery edges (`core/sensing.py → ops`, `core/temporal/spine.py → eval`);
the original 106 were config 90 / ops 8 / eval 7 / agents 1 — config injection was the bulk (hence
bp-067's config-split). Meanwhile `core/scope.py`, `core/complex/`, `core/graph/composed.py` already
import stdlib+numpy and nothing else. **Reframe: the finding-0103 cleanup is not stain-removal, it
is excavation — revealing the inner core that is already in there.** A positive telos for a
multi-session grind.

**The membership criterion must be mechanical, never taste.** Proposed: *inner core = the maximal
import-closed subset of `core/**` over {stdlib, pinned pure math libs (numpy/scipy), inner core
itself}* — a fixed-point computation the existing AST scanner
(`tests/unit/test_core_self_containment.py`) can run today. No judgment calls; a new module is inner
iff it satisfies the predicate.

**Enforcement: two nested ratchets + a direction law** (structural-enforcement rule — a property is
only real when a test proves it):
1. **Inner ring** (new test): members import ⊆ {stdlib, pinned math 3p, inner ring}. **Born green**
   — enforceable the day it is written; a win banked immediately, no cleanup precondition.
2. **Outer ring** = the EXISTING ratchet, unchanged, still counting 19 → 0 over all of `core/`.
   **Explicit no-laundering clause:** the split must never redefine a violation away — moving a
   violating file "outward" changes nothing; the outer ratchet binds all of core regardless of ring.
3. **Direction law:** outer imports inner; never the reverse.

**The ring boundary runs through modules, not packages — and that is fine.** Example the fixed
point will surface: `core/graph/sigma_star.py`'s math (`build_max_spanning_tree`, `sigma_star`) is
pure, but `acquire_mirror_cut` reaches the spine (which today reaches eval). The fix is bp-065's
move one ring deeper: **math stays inner; acquisition/assembly moves outward.** Similarly
`core/dreaming/`: `cluster.py` math is inner-eligible; pipeline/persistence is outer. Directory
repackaging (`core/kernel/` vs `core/machinery/`) is optional cosmetics, later; the enforcement is
the import test, not the layout.

**The taxonomy connection (dn-agent-taxonomy).** "The dreamer is core-resident" refines to
*outer-core-resident*: the dreamer and the librarian are **clients of the algebra, not the algebra**.
The inner core is not an agent — it is the vocabulary agents are written in; nobody grants you
arithmetic. Completes a symmetry: the data side already has two-tier sacredness (𝔇 ungrantable at
the center, grantable strata around it); inner/outer gives the code side the same geometry.
CONSTITUTION.md is to data what the inner core is to machinery: the fixed points.

```capsule
topic: inner-outer-core
date: 2026-07-18   # owner local; appended 2026-07-19 UTC

decisions:
  - The membership criterion is MECHANICAL: inner core = the maximal import-closed subset of
    core/** over {stdlib, pinned pure math 3p, itself} — computed, never curated.
  - Two nested ratchets + a direction law (outer→inner only); the inner ring is born green; the
    existing 19-count outer ratchet is UNCHANGED — the split is explicitly not a laundering path
    for finding-0103.
  - Rings are per-module, not per-package; directory moves are cosmetic and deferred.

parked:
  - decision: directory repackaging (core/kernel/ vs core/machinery/)
    default: rings enforced by the import test only; files stay where they are
    re_entry: the outer ratchet reaches 0, or the ring map stabilizes across several plans
  - decision: whether "librarian" names the curator or a retrieval-serving agent
    default: vocabulary only; no code implication yet
    re_entry: the dn-inner-outer-core design pass

open_questions:
  - The exact fixed-point membership list (compute at build time; expected seed — scope.py,
    agent_scope.py, complex/*, graph/composed.py, recursion; surfaced splits — sigma_star math vs
    cut acquisition, dreaming/cluster vs pipeline).
  - Does the inner ring also forbid I/O/clock reads beyond imports (a purity predicate), or is
    import-closure sufficient for v1?
  - Interaction with the 4 strata-overlapping inversions parked under finding-0103.

next_steps:
  - Design pass drafts dn-inner-outer-core (can ride the same fable pass as dn-decision-routing).
  - At build: compute the fixed point; write the inner-ring test (born green); state the direction
    law; annotate module headers. Small plan, low blast radius.
  - Sequencing: does NOT preempt the diamond — bp-069 remains the lead build.

references:
  - docs/findings/finding-0103.md                # the ratchet; the cleanup this reframes as excavation
  - tests/unit/test_core_self_containment.py     # the scanner the fixed point reuses
  - docs/design-notes/agent-taxonomy.md          # "core-resident" refines to outer-core-resident
  - docs/design-notes/capability-scope-algebra.md
  - docs/build-plans/bp-065/plan.md              # precedent: math→core; here, math→inner
  - core/scope.py · core/complex/ · core/graph/composed.py   # the already-pure seed
  - core/graph/sigma_star.py · core/dreaming/    # where the ring runs through a module
  - docs/brainstorms/dyadic-epistemology.md      # the sibling session's capture (same evening)
```

## 2026-07-20T21:28Z (session-39, fable — owner directive: the repo structure reflects the split)

Owner, in chat while dispatching the design pass: *"I do want the eventual repo structure to
reflect the separation."* This lifts the 2026-07-19 parked item (directory repackaging as
"optional cosmetics, later") into a decided end-state: the physical layout WILL eventually mirror
the inner/outer rings. What stays open is the concrete layout and its sequencing — that is now a
first-class obligation of the design pass, not an afterthought.

```capsule
topic: inner-outer-core
date: 2026-07-20

decisions:
  - The eventual repo structure REFLECTS the inner/outer separation (owner, session-39). The
    2026-07-19 parked decision "directory repackaging (core/kernel/ vs core/machinery/)" is
    decided in DIRECTION — physical separation is the committed end-state, no longer optional
    cosmetics. Layout and sequencing remain design-pass questions.

open_questions:
  - The concrete target layout (core/inner/ + core/outer/? kernel/ vs machinery/? something else)
    and migration sequencing (before/after the outer ratchet reaches 0; before/after the ring map
    stabilizes) — the dn-inner-outer-core pass must answer both with a migration path.

next_steps:
  - The dn-inner-outer-core fable design pass (dispatched this session) treats target layout +
    migration path as first-class sections of the note.

references:
  - docs/brainstorms/hypothetical-subspace.md   # captured same session — first concrete outer-core consumer
```

## 2026-07-20T22:08Z (session-39, fable — owner ruling on the draft's open predicate decision: v2)

The dn-inner-outer-core draft (`fde4326`) left ONE predicate ruling to the owner: v1
(∖ network stdlib; 51 members, sqlite store layer inside) vs the parked P1/v2 (further ∖ sqlite3;
~29 members — "the math and the sacred boundaries"). Owner, in chat after the diff was laid out:
*"i do like v2 more."*

```capsule
topic: inner-outer-core
date: 2026-07-20

decisions:
  - The inner-ring predicate is V2 (owner ruling, session-39): base = (stdlib ∖ NETWORK_MODULES
    ∖ {sqlite3}) ∪ {numpy, scipy}, strict semantics — the ring is the math/algebra/sacred-boundary
    vocabulary of the founding language, not the austere plumbing. The wider network-only ring
    (v1, 51 members) is recorded as the rejected alternative with a re-entry, not deleted.
  - Still import-grain, still computed-never-curated; the honest caveat carries forward — v2 is
    NOT call-grain effect-free (e.g. rawstore touches disk via pathlib, config.loader reads env);
    a full purity predicate remains a parked v3.

next_steps:
  - Re-cut the draft note to adopt v2 before ratification: recompute the fixed point at HEAD,
    rewrite the membership appendix and the affected sections; ratification remains owner-by-hand.
```

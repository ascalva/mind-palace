---
type: finding
id: finding-0182
status: open             # open → routed → resolved | promoted
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/build-plans/bp-104/plan.md
  - ops/import_lint.py
  - tests/unit/test_core_self_containment.py
  - docs/findings/finding-0103.md
  - docs/design-notes/inner-outer-core.md
  - docs/book/chapters/02-architecture.tex
ftype: discovery
origin_plan: bp-104
route: orchestrator
resolution: null
---

# The import firewall's global claim is conditional on core self-containment — the two ratchets are one theorem

## What

Writing Chapter 2's formalisation of the import firewall surfaced a composition
that the record states in two places but never joins.

`ops/import_lint.py` motivates itself with a **closure** claim (docstring, verified
at `009b726`):

> "I2 is a property of the *import closure*: if no module under `core/` can reach a
> network-capable module, then **no egress path exists regardless of edge
> behavior** — composition cannot create one."

The conditional is true. But the check the lint actually performs is **local**: one
AST walk per file, over that file's **direct** imports (`scan_file` →
`_imported_names`; `scan_core` iterates `core.rglob("*.py")` and calls `scan_file`).
It does not compute a closure. So what the lint discharges is:

- every **direct** core import of `edge` / `cloud` — forbidden outright;
- every **direct** core import of a `NETWORK_MODULES` root — forbidden outside the
  two audited loopback files.

The antecedent of the docstring's conditional ("no module under `core/` can
**reach** a network-capable module") follows from that local check **only under an
extra hypothesis**:

> (⋆) every module core reaches outside `core/` is stdlib or a pinned,
> side-effect-free third-party library.

If a core module imports, say, `ops.something` and that module imports `httpx`,
the local check is green and a `core → ops → httpx` reach-path exists. The lint's
own honest sentences are all direct-import claims and do not overclaim ("Every
*other* core module is thereby statically proven free of networking **imports**") —
so this is not a defect in the lint's text. It is a **missing composition** in the
record.

And (⋆) is exactly the invariant of
`tests/unit/test_core_self_containment.py` — which is **red by design** (owner
directive, finding-0103): core still imports from sibling packages, and the test is
a ratchet whose count may only decrease (`dn-inner-outer-core` §2.4-C records it
counting 19 → 0 over all of `core/`; a rough re-scan at `009b726` found the same
order of magnitude, with `ops` and `eval` dominating).

**Therefore:** until that ratchet reaches zero, the sealed core's *static* network
isolation (Invariant 1/2, BUILD-SPEC §3) is a **conditional** result, and the open
condition is finding-0103's cleanup programme.

## Why it matters

finding-0103 has been carried as a **hygiene / architecture-cleanliness** item —
"core is the processing unit; everything else is machinery around it," coupling
the sacred to the machinery's churn. This finding reclassifies part of its value:
it is also the **discharge condition for a safety invariant**. That should raise
its priority relative to other cleanup work, and it gives the remaining inversions
a sharper acceptance criterion than "fewer imports."

Two mitigations already exist and are why this is a `discovery` and not a
`blocker`: the runtime egress guard (`core/sealing.py`, fail-closed, process-wide)
and the kernel `pf` anchor on the `ouroboros` uid
(`ops/network/ouroboros-egress.pf.conf`, `dn-plane-principals` §3.4) both hold the
property **unconditionally** and independently of the import graph. The static
tier is the one carrying the condition. That is also the honest answer to "why keep
three layers" — the layers are not redundant while one of them is still
conditional.

## Proposal

Three cheap, separable moves — none of them a design change:

1. **Record the composition where a reader will meet it.** A line in
   `ops/import_lint.py`'s docstring stating that the closure claim is discharged
   modulo `tests/unit/test_core_self_containment.py`, and the reciprocal line in
   that test's docstring. (Builder-resolvable; needs a plan naming those two files.)
2. **Consider closing it structurally instead.** The strongest version of the lint
   walks the closure over first-party modules rather than direct imports; then the
   claim is unconditional today and the ratchet becomes an independent hygiene
   item again. Cost: the lint must resolve first-party imports transitively — the
   `tests/unit/test_inner_ring.py` fixed-point scanner already does exactly this
   kind of walk, so the technique is in-tree.
3. **Re-weight finding-0103** on the board as a safety-discharge item.

Recorded in the book as written: Chapter 2 §"The import firewall" now states the
local invariant, proves what it gives (`Proposition 2.1`), names (⋆) explicitly,
and gives the unconditional closure result as a limit
(`Proposition 2.2`) — rather than repeating the closure claim as if discharged.

## Re-entry condition

N/A — nothing in bp-104 is parked on this. For the proposal: item 1 is a papercut
that can ride any plan touching `ops/**`; item 2 is a design question for the
owner (is a closure-walking lint worth its cost, or is the ratchet the intended
path?); item 3 is a board re-weighting at the next `/triage`.

## Routing

`discovery` bearing on **design** → the orchestrator. Owner input is wanted for
proposal 2 only; proposals 1 and 3 are orchestrator/builder work.

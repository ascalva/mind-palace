---
type: build-plan
id: bp-083
track: inner-outer-core
status: complete
design_ref:
  - docs/design-notes/inner-outer-core.md
contract: builder
write_scope:
  - core/rings.py
  - tests/unit/test_inner_ring.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual:
    model: opus            # claude-opus-4-8[1m], tier verified via completion usage
    tokens: 97778
    tool_calls: 65
    duration_min: 42
    ratio: 0.39            # well UNDER — born-green additive is cheap; F6 satisfied by construction (computed==29 at HEAD, no hand-edit)
    session_delta: "weekly all-models pool; ran parallel with bp-085/bp-086; duration inflated by full-suite contention (≤2-builder lesson)"
depends_on: []
parallelizable_with: [bp-085, bp-087]
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/inner-outer-core.md
  - tests/unit/test_core_self_containment.py
  - ops/import_lint.py
  - docs/findings/finding-0103.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — M0: enforce the two-ring refinement in place (born-green inner ratchet)

> Graduated from ratified `dn-inner-outer-core` §2.4 / §2.7-M0 / §3. The FIRST of the two plans
> the note licenses (S1 = bp-084 is the SECOND, strictly after this). Additive-only: two new
> files, no file moves (that is M2, later), no store change, no behavior change, the outer ratchet
> untouched. The map is **recomputed at build HEAD** — Appendix A's 29-member list is the note's
> *expectation*, never authority (falsifier F6).

## 0. Mode & provenance

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.
`proposed → ready` stays owner-only, by hand. Authority-to-act (the owner blessing this plan
ready) is separate from the readiness blessing; no agent flips readiness. This plan preempts
nothing in the sequenced queue — it rides behind the lead build (the note's pin: the diamond
remains lead; M0 is additive and non-urgent).

## 1. Objective

Land `core/rings.py` (the declared inner-ring map, forced to equal a computation) and
`tests/unit/test_inner_ring.py` (the born-green strict-v2 fixed-point ratchet), so that every
future change to inner-ring membership is a reviewable one-file diff — with zero file moves,
zero behavior change, and the existing outer ratchet left exactly as it is.

## 2. Context manifest

Read these whole, in order, before any work:

1. `docs/design-notes/inner-outer-core.md` — the whole note; §2.1 (the v2 predicate: base =
   `(stdlib ∖ NETWORK_MODULES ∖ {sqlite3}) ∪ {numpy, scipy}`), §2.3 (STRICT closure semantics),
   §2.4 (the three assertions, verbatim — this plan's acceptance), §2.7-M0, Appendix A (the
   *expected* 29 — expectation, not authority).
2. `tests/unit/test_core_self_containment.py` — the outer scanner this plan MIRRORS but does not
   touch: the AST walk (`ast.Import` / `ast.ImportFrom` with `level == 0`), the repo-root marker
   walk, the `test_scanner_sees_the_known_violation_set` honesty pattern. The inner scanner is a
   deliberate second, independent copy (§2.4's named DRY exception) — do NOT refactor a shared
   helper.
3. `ops/import_lint.py:44-60` — `NETWORK_MODULES` (the audited ban set the predicate's first
   subtraction reuses) and `NETWORK_ALLOWLIST` (the two network-capable core files).
4. `core/__init__.py` — confirm it is import-free (the strict-semantics structural precondition,
   §2.3): a single impure import there collapses the fixed point.

## 3. Investigation & grounding

Not greenfield — the test reads all of `core/**` and mirrors an existing scanner. Grounded at
HEAD (`d08da37`):

- **Q1 — does the outer scanner's AST pattern transfer?** Yes. `_core_sibling_imports`
  (`test_core_self_containment.py:52-77`) walks `ast.Import` and `ast.ImportFrom` (`level == 0`),
  taking the first dotted segment as the root; `ast.walk` sees function-body (lazy) and
  `TYPE_CHECKING` imports — exactly the counting semantics §2.1 requires. The inner scanner adds
  **relative-import resolution** (the outer scanner skips `level > 0` as intra-core; the inner
  scanner must resolve them to full module names to compute the closure) and **closure iteration
  to a fixed point** over the admissible base.
- **Q2 — is `NETWORK_MODULES` importable by a test?** Yes — `ops/import_lint.py:44`. Tests are
  machinery; the `test → ops` arrow is allowed (§2.4). `core/rings.py` itself imports it **not**:
  the map is stdlib-only and declares `PLUMBING_STDLIB = {"sqlite3"}` beside `MATH_3P =
  {"numpy","scipy"}`; the network subtraction stays sourced from `ops.import_lint.NETWORK_MODULES`
  in the *test's* computation only (the map's one owner-ruled parameter, sqlite3, has its home in
  `rings.py`; the already-audited network set keeps its single home in `ops`).
- **Q3 — is `core/__init__.py` import-free today?** Must be verified at build start (a docstring,
  zero imports — §2.3). If not, the fixed point collapses and assertion B1 goes catastrophically
  red; that is a real finding, not a test bug (do not paper over it).
- **Q4 — is the expected membership 29?** The note computed 29 strict at `97c245c`. **Recompute at
  build HEAD.** If HEAD differs (a module gained/shed an inadmissible import since), the *computed*
  set is authoritative and `INNER` is written to match it; Appendix A is the sanity check, not the
  target (F6).

**Additional risks surfaced:** string-based dynamic imports (`importlib.import_module`) are
invisible to AST scanning — the shared blind spot F8 names; both scanners carry it, documented,
not worked around here.

## 4. Reconciliation

- `tests/unit/test_core_self_containment.py` — the outer ratchet — is **EXTENDED by
  cross-reference, never edited**: the new module's docstring cross-references it as the
  independent second scanner, and `test_inner_ring.py`'s honesty guard mirrors (does not import)
  its `test_scanner_sees_the_known_violation_set` pattern. **No banner-correction anywhere** — this
  plan corrects no committed code; it is purely additive. (§2.4-C: the outer ratchet is UNCHANGED.)

## 5. Write scope

Exactly two new files: `core/rings.py` and `tests/unit/test_inner_ring.py`. Deliberately OUT of
scope: `tests/unit/test_core_self_containment.py` (pinned unchanged — pillar 2), `ops/import_lint.py`
(the network set keeps its home), every `core/**` source file (M0 moves nothing; promotions are
S1's and later waves'), and the foundation denylist. A denial here means the plan overreached —
narrow it or file a finding, never route around.

## 6. Interfaces pinned inline

**`ops.import_lint.NETWORK_MODULES`** (`ops/import_lint.py:44`, the test's computation imports it):
```python
NETWORK_MODULES: frozenset[str] = frozenset({ ... })   # the audited network-capable stdlib set
```
**`core/rings.py` declares (map forced to equal the computation):**
```python
INNER: frozenset[str]              # module names (e.g. "core.scope"), not paths — survives M2 renames
MATH_3P: frozenset[str] = frozenset({"numpy", "scipy"})
PLUMBING_STDLIB: frozenset[str] = frozenset({"sqlite3"})   # the v2 owner-ruled subtraction (§2.1)
```
**The predicate (§2.1), strict semantics (§2.3):** admissible base =
`(stdlib ∖ NETWORK_MODULES ∖ PLUMBING_STDLIB) ∪ MATH_3P`; `INNER` = the maximal import-closed
subset of `core/**` over that base, where a module's dependencies include (strict) every ancestor
package `__init__` of everything it imports.

**The three assertions (§2.4-B, verbatim intent):**
1. `test_inner_ring_is_the_computed_fixed_point` — computed == declared, both directions.
2. `test_outer_never_imported_by_inner` — the direction law, per-member, its own message.
3. `test_scanner_sees_known_impurities` — the honesty guard: computed exclusions include
   `sealing` (socket), `stores.chatlog` (sqlite3), `stores.vectorstore` (pyarrow),
   `temporal.spine` (eval), `complex.spectral` (sknetwork), and the computed set is non-trivially
   large.

## 7. Items

### Item 1 — `core/rings.py`: the ring-map declaration (recomputed at HEAD)
- **Objective:** a stdlib-only, inner-by-construction module declaring `INNER`, `MATH_3P`,
  `PLUMBING_STDLIB` — `INNER` set to the strict-v2 fixed point computed at build HEAD.
- **Files:** `core/rings.py` (new).
- **Acceptance test:** the module imports with zero non-stdlib deps; `INNER` is a `frozenset[str]`
  of `core.*` module names; item 2's equality assertion is green against it.
- **Falsifier (F6):** if `INNER` is transcribed from Appendix A rather than recomputed and the
  equality test lands red at HEAD, the map was computed at a stale tree — recompute, never
  hand-edit `INNER` toward green.
- **Invariant(s):** `core/rings.py` is itself inner (stdlib-only); it wires no read path.
- **Touches stored data?** No.
- **Parallelizable?** No (item 2 depends on it). **Depends on:** none.

### Item 2 — `tests/unit/test_inner_ring.py`: the born-green fixed-point ratchet
- **Objective:** recompute the strict-v2 fixed point at test time and assert the three §2.4-B
  properties; born GREEN.
- **Files:** `tests/unit/test_inner_ring.py` (new). The fixed-point computation lives IN this
  module (P4: not extracted to `ops/` until a second consumer exists).
- **Acceptance test:** `uv run pytest tests/unit/test_inner_ring.py` is green at HEAD; all three
  named tests pass; assertion 3 confirms the five known exclusions and a non-trivial `|INNER|`.
- **Falsifier (F4):** an inner→outer import observed with assertion 1 green ⇒ the scanner lies;
  assertion 2's per-member direction-law tooth must catch it — if it doesn't, extend the honesty
  guard, do not relax.
- **Invariant(s):** the outer ratchet is not imported, refactored, or weakened; a genuine red is a
  finding, never silenced with xfail/skip/allowlist.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** item 1.

## 8. Math carried explicitly

- **The inner ring = the maximal import-closed subset of `core/**` over the admissible base** —
  *measures:* which core modules pull in only {admissible base ∪ inner} at runtime (strict
  semantics: ancestor `__init__`s counted). *valid when:* the import graph is statically visible
  to AST (absolute + resolved-relative + lazy + TYPE_CHECKING all counted). *fails its keep if:* a
  string-`importlib` import smuggles an inadmissible dep past the scanner (F8) — then the computed
  membership overstates purity and the scanner must grow a `Call`-node check for `importlib` in
  inner members.

## 9. Non-goals

No file moves (M2). No promotions (S1 and later waves add the +7 and the packaging-debt 13). No
change to the outer ratchet, the import firewall, `MIRROR_READABLE`, the denylist, or any store.
No call-grain purity analysis (v3 is parked, P1). No extraction of the fixed-point computation to
`ops/` (P4).

## 10. Stop-and-raise conditions

- Assertion 1 red at HEAD after an honest recompute ⇒ **stop**: either `core/__init__.py` is not
  import-free (a real regression — file a finding) or the note's predicate transcription is wrong
  (re-ground §2.1); never hand-edit `INNER` toward green (F6).
- Any temptation to touch `test_core_self_containment.py` ⇒ stop; it is pinned unchanged.
- A computed `|INNER|` wildly off Appendix A's 29 (e.g. < 20 or > 40) ⇒ stop and reconcile before
  writing the map — the predicate or the closure semantics is likely mis-implemented.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Extract the fixed-point computation to `ops/` (P4) | lives in `test_inner_ring.py` | shared helper (a single scanner bug could blind both rings — §2.4's redundant-sensor argument) | a second consumer materializes (statusline gauge, M2 tooling) |
| v3 call-grain purity (P1) | import-grain only | forbid disk/env/clock calls (brittle, large false-positive surface, no consumer) | falsifier F1 fires |
| Physical `core/kernel/` move (M2) | enforce-in-place; no moves | move now (churn without enforcement gain) | per-wave stability gates (§2.7-M2), a later plan |

## 12. Dependency & ordering summary

Two items, strictly sequential (item 2 depends on item 1). No dependency on any other plan;
**S1 (bp-084) depends on THIS** (S1 is the first promotion wave, +7 → 36, and its map diff lands
against the `INNER` this plan creates). Parallelizable with bp-085 (G-A, eval-side) and bp-087
(AL-2, read-only) — disjoint write scopes. Blast radius: purely additive (read-only sensing over
`core/**`; two new files).

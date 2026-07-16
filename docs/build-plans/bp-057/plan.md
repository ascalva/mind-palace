---
type: build-plan
id: bp-057
alias: sigma-gate
status: proposed
design_ref:
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md   # RATIFIED — §2.5 the strength→surfacing gate + the F9 validation protocol + the gate falsifier (FB-3)
contract: builder
write_scope:
  - eval/harness/gate.py
  - tests/quality/test_sigma_gate.py
  - tests/quality/fixtures_sigma_gate.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 220k
depends_on: [bp-050, bp-054]
parallelizable_with: [bp-055, bp-056]
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/dreamer-quality-suite-evaluation.md   # F9 — the validation battery + the F1-variant fixtures this reuses
  - docs/design-notes/recursive-strata.md                   # I1 — the boundary the gate must never cross
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — FB-3: the strength→surfacing gate, F9-validated (SETTLED / HUNCH / RETAINED)

## 0. Mode & provenance
Graduated from RATIFIED `dn-sigma-fibers` §2.5. **The conditional plan of the wave: the gate
SHIPS ONLY IF the validation criteria hold** — a completed run of this plan that records
no-signal-at-this-scale and parks is a SUCCESS, not a failure (dn-evaluation-harness §2.3
discipline). I1 is absolute: the gate filters SURFACING of proposed candidates only — never a
weight, never a confidence, never a promotion.

## 1. Objective
(1) `eval/harness/gate.py`: tier assignment over bp-050's per-claim fibers — `pers ≥ θ_strong ⇒
SETTLED`, `θ_weak ≤ pers < θ_strong ⇒ HUNCH` (capped, labelled), `else RETAINED` (ledger-only);
confidence orders WITHIN a tier; θ defaults `θ_weak = 2/m`, `θ_strong = 0.5` in a THRESH-style
dict (tuning, not code). (2) The F9 validation protocol as executable tests over noise +
planted-structure fixtures, with the ship/park decision computed, recorded, and enforced.

## 2. Context manifest (read in order)
1. `docs/design-notes/sigma-fibers-and-multiscale-dreaming.md` §2.5 (WHOLE — the rule, the
   boundary conditions, the validation protocol, the gate's three-clause falsifier).
2. bp-050's merged `eval/harness/fibers.py` — `ClaimFiber` (the gate's input type).
3. `tests/quality/test_dreamer_quality.py` — the THRESH table shape (:456) + the F1
   noise/planted fixture patterns this plan's fixtures extend (same statistical philosophy:
   bounds and relationships, never exact values).
4. `core/dreaming/adjudicator.py:8-24` — confidence c(κ) (read-only; the WITHIN-tier ordering
   key; never multiplied with pers — the one-scalar prohibition, verbatim).
5. `docs/design-notes/recursive-strata.md` §4 I1 + §9 (the never-list this plan must re-assert
   in its own tests).

## 3. Investigation & grounding
- **The gate consumes report-layer fibers, mutates NOTHING:** no ledger write, no eval-store
  write beyond its own validation readings, no DreamLogEntry change (SF-d parked), no lever
  registration (θ lives in the THRESH dict per the note; promotion to `ops/levers.py` is a
  separate future owner-visible act).
- **Fixtures:** σ-sweep the F1-variant corpora (pure noise; planted two-cluster structure with
  known cosines) through the BUILT ShadowRunner at 3–5 grid points in-memory — cheap,
  deterministic, model-free; the fibers consumer then produces the ClaimFibers the gate tiers.
- **The ship criteria (note §2.5, verbatim — computed by the test, recorded in the journal):**
  (i) noise-fixture SETTLED-tier rate ≈ 0; (ii) planted claims reach SETTLED; (iii) tiering
  strictly improves surfaced precision over the best single-σ baseline on the same fixtures.

## 4. Reconciliation
None expected. If criterion (ii) fails BECAUSE planted features morph across σ (claim-identity
flicker), that is SF-a's re-entry — file the finding naming it, park the gate, do NOT loosen θ
to force a pass.

## 5. Write scope
The three files in frontmatter. **OUT:** `fibers.py` (bp-050's), `registry.py` (bp-054's),
`ops/levers.py`, the REPL/report wiring (a later E6 tenant plan), `core/**`, denylist.

## 6. Interfaces pinned inline
```python
# eval/harness/gate.py
class Tier(Enum): SETTLED = "settled"; HUNCH = "hunch"; RETAINED = "retained"

GATE_THRESH: dict[str, float] = {"theta_weak_cells": 2.0,   # θ_weak = 2/m — at least 2 grid cells
                                 "theta_strong": 0.5}        # tuning, not code (THRESH lifecycle)

@dataclass(frozen=True)
class TieredClaim:
    fiber: ClaimFiber            # bp-050's type, verbatim
    tier: Tier
    within_tier_rank: float      # = adjudicator confidence c(κ); NEVER combined with pers

def assign_tiers(fibers: Sequence[ClaimFiber], *, m: int,
                 confidence: Mapping[str, float]) -> list[TieredClaim]
def hunch_section(claims: Sequence[TieredClaim], *, cap: int) -> list[TieredClaim]  # labelled, capped
```

## 7. Items
### Item 1 — tier assignment + the I1 guard tests
- **Acceptance:** `uv run pytest tests/quality/test_sigma_gate.py -q` (unit half) green:
  boundary claims tier correctly at θ edges; ordering within a tier follows confidence alone
  (a high-pers low-confidence claim never outranks within-tier by pers); RETAINED claims appear
  in NO surfaced output; the module writes to no store (assert: gate.py imports no store
  writer); the one-scalar prohibition asserted (no code path multiplies pers into confidence —
  grep-test).
- **Falsifier:** any write path; any pers×confidence scalar; a RETAINED claim surfacing.
### Item 2 — the F9 validation protocol + the ship/park decision
- **Acceptance:** the validation tests run the §3 fixture sweeps end-to-end and COMPUTE the
  three criteria; the results land as keyed readings (`sigma_gate.validation.*`) + a journal
  record. **If all three hold:** the gate's quality tests join the suite green. **If any
  fails:** the plan completes by recording the failing clause, parking the gate behind the
  matching re-entry (SF-a for identity-flicker; corpus-growth for no-signal), and the surfaced
  API raises `GateNotValidated` — never a silent ship.
- **Falsifier (the note's, verbatim):** noise claims reaching SETTLED at ≥ the single-σ
  baseline rate with the tests green — the validation itself is broken; STOP.

## 8. Math carried explicitly
The rule (ratified §2.5, hold exactly): two thresholds partition [0,1] of pers; lexicographic
two-axis ordering (tier by pers; rank by c(κ)); no scalar fusion. Validation criteria (i)–(iii)
as §3. θ defaults provisional — calibration data is this plan's own validation output.

## 9. Non-goals
No REPL/report UI wiring (E6 tenant, later plan). No live dreamer change. No θ levers in
`ops/levers.py`. No claim matching (SF-a). No promotion/verdict logic (I1 — never).

## 10. Stop-and-raise
Criterion failure → park-and-record per §7 Item 2 (a sanctioned outcome, not an error). Any
pressure to weaken a criterion to ship → STOP, that is the apophenia gate failing itself. Any
blessing: never.

## 11. Parked decisions
| Decision | Default | Re-entry |
|---|---|---|
| θ as registered levers | THRESH dict | owner wants sweep-driven θ tuning (then an owner-visible lever plan) |
| REPL surfacing wiring | none (API + report only) | E6 tenant plan |
| v2 claim matching | not built | SF-a's trigger via criterion (ii) |

## 12. Dependency & ordering
Depends bp-050 (ClaimFiber) + bp-054 (registered names for its validation readings). Parallel
with bp-055/bp-056 (disjoint). Blast radius: additive eval-side; the SHIP decision is
data-gated by design.

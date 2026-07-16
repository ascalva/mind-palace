---
type: build-plan
id: bp-055
alias: certified-cuts
status: proposed
design_ref:
  - docs/design-notes/global-event-clock.md   # RATIFIED — §2.4 GC-N3 certified cuts + the cut falsifier (GC-3)
contract: builder
write_scope:
  - core/temporal/spine.py
  - tests/unit/test_cuts.py
  - tests/integrity/test_cut_soundness.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 180k
depends_on: [bp-053]
parallelizable_with: [bp-056, bp-057]
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/cross-strata-dreamer.md   # G3 — the consumer this satisfies (its own G-chain still fronts any dreamer build)
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — GC-3: certified quiescent cuts (the SLICE rule completed for non-repo strata)

## 0. Mode & provenance
Graduated from RATIFIED `dn-global-event-clock` §2.4. Extends the spine (sequential after
bp-053; same file). **Design pin that keeps wave 3 parallel-safe: `Scope.cut` in
`core/scope.py` is NOT touched** — a `CertifiedCut` is itself `Hashable` and rides in the
existing opaque `cut` field; the typed object lives spine-side.

## 1. Objective
`CertifiedCut` in `core/temporal/spine.py`: a per-store frontier vector + a certificate
(commit | trough-quiescence | handoff-empty), certificate composition for cross-strata cuts,
down-set materialization, and the crossing-edge soundness test as a non-skippable integrity
tooth.

## 2. Context manifest (read in order)
1. `docs/design-notes/global-event-clock.md` §2.4 (WHOLE — GC-N3, the three certificates, the
   cut falsifier), §2.2 (the incompleteness law that makes certification necessary).
2. `core/temporal/spine.py` as merged by bp-053 (`frontier`, `p`, `n_s`).
3. `core/scope.py:441-480` — `SliceError` + the `cut` field (READ-ONLY — understand what a cut
   must satisfy; never edit).
4. `core/sensing.py:228-240` — the handoff directories (the handoff-empty certificate's
   observable).
5. `scheduler/__init__.py` — the queue-ownership surface the trough-quiescence certificate
   reads (read-only; if no clean read exists, see §10).

## 3. Investigation & grounding
- A cut is a DOWN-SET of `(Ev, ≼)`; the frontier vector generates it; the certificate is what
  makes it sound despite `≼_derived ⊆ ≼_true` (the incompleteness law — computed-but-uncertified
  cuts are REFUSED, not warned).
- **Certificates:** commit (repo-backed strata; atomic by git); trough-quiescence (queue empty
  between jobs — read from the scheduler's own state, never inferred); handoff-empty
  (`requests/` and `observations/` both empty). A cross-strata cut COMPOSES all applicable
  certificates; a missing certificate for an in-scope stratum ⇒ construction refuses.

## 4. Reconciliation
None expected. If the scheduler exposes no readable quiescence fact → file a `codebase` finding
and ship commit+handoff certificates only (the trough certificate parks with the finding as
re-entry) — never fake quiescence.

## 5. Write scope
The three files in frontmatter. **OUT:** `core/scope.py` (the pin above), `core/sensing.py`,
`scheduler/**` (read-only), denylist.

## 6. Interfaces pinned inline
```python
class Certificate(Enum): COMMIT = "commit"; TROUGH = "trough-quiescent"; HANDOFF = "handoff-empty"

@dataclass(frozen=True)
class CertifiedCut:                       # Hashable — rides in Scope.cut UNCHANGED
    frontier: tuple[tuple[str, int], ...] # sorted (store, position) pairs
    certificates: frozenset[Certificate]
    evidence: tuple[str, ...]             # commit SHA / trough id / handoff listing hash

class Spine:
    def cut_at(self, *, strata: frozenset[str]) -> CertifiedCut     # refuses if any needed certificate absent
    def downset(self, cut: CertifiedCut) -> frozenset[str]          # the event down-set
    def crossing_edges(self, cut: CertifiedCut) -> list[tuple[str, str]]   # MUST be [] — the falsifier
```

## 7. Items
### Item 1 — CertifiedCut + certificates + composition
- **Acceptance:** `uv run pytest tests/unit/test_cuts.py -q` green: `cut_at` over injected
  fakes composes the right certificate set per strata; a stratum with no available certificate
  ⇒ refusal with a clear message; `CertifiedCut` hashes (rides in `Scope.cut` — construct a
  multi-stratum `Scope` with it and no `SliceError` raises).
- **Falsifier:** a cut constructed without its needed certificate; a certificate asserted from
  wall-time or inference rather than the named observable.
### Item 2 — the soundness tooth
- **Acceptance:** `uv run pytest tests/integrity/test_cut_soundness.py -q` green ON THE REAL
  STORES: for cuts taken at the current commit+handoff state, `crossing_edges == []`; a
  synthetically corrupted cut (frontier moved past a referenced event) is DETECTED.
- **Falsifier:** a certified cut with a crossing g-edge on main (certification bug — merge
  blocks).

## 8. Math carried explicitly
Down-set: `D(cut) = {e : ∀ stores, pos(e) ≤ frontier(store)}` closed under ≼-predecessors;
soundness: no edge `(a,b)` with `b ∈ D`, `a ∉ D` (the §2.4 falsifier, verbatim). Composition:
certificates for all strata whose stores intersect the frontier.

## 9. Non-goals
No `Scope.cut` type change (the pin). No T-meet work (bp-056). No marker-passing protocol
(GC-c parked — quiescence certificates only). No cross-strata dreamer anything (its G-chain).

## 10. Stop-and-raise
No readable scheduler quiescence fact → finding + park the TROUGH certificate (ship the other
two). Crossing edge found on a certified cut in the wild → STOP, `codebase` finding (data
corruption class). Any blessing: never.

## 11. Parked decisions
| Decision | Default | Re-entry |
|---|---|---|
| marker-passing cuts | quiescence certificates (GC-c) | a writer outside the scheduler's view |
| typed Scope.cut field | opaque Hashable carries CertifiedCut | a second cut consumer wants the type in core/scope.py (then a small owner-visible plan) |

## 12. Dependency & ordering
Depends bp-053. Parallel with bp-056/bp-057 (disjoint files). Satisfies cross-strata G3 (the
gate chain's OTHER gates remain). Blast radius: additive read-side + integrity tooth.

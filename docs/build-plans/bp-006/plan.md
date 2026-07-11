---
type: build-plan
id: bp-006
status: proposed
design_ref:
  - docs/design-notes/type-system-as-core-audit.md
contract: builder
write_scope:
  - "core/**"
  - "pyproject.toml"
  - "docs/findings/**"
  - "docs/build-plans/bp-006/**"
session_budget: 1
depends_on: []
parallelizable_with: []
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/audits/mypy-baseline-2026-07-11.md
  - docs/findings/finding-0026.md
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Tier-1 type audit: triage core's 193 errors, wrap the untyped boundaries, drive strict green

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated from the ratified `type-system-as-core-audit.md` (owner blessing 2026-07-11,
commit `10c9a66`) — this is the note's **B-1 back half**: the config and baseline
measurement already landed (`e84f6a7`; 463 errors inventoried, 193 in core). This plan
is the *audit proper* — triage and remediation. Authority-to-act is the owner's
ratification; the readiness blessing (`proposed → ready`) is the owner's hand, item-by-item.

## 1. Objective

Every `core/` mypy error is triaged into T1/T2/T3 per §2.3 — each T1 filed as its own
finding, each T3 ignore warranted and coded — and Tier 1 runs strict-green.

## 2. Context manifest

1. `docs/design-notes/type-system-as-core-audit.md` — the ratified decision; §2.1–§2.5 govern.
2. `docs/audits/mypy-baseline-2026-07-11.md` — the baseline inventory this plan consumes.
3. `pyproject.toml` — `[tool.mypy]` two-tier config (Tier-1 strict components under `core.*`).
4. `core/stores/vectorstore.py` — the top hotspot (15 errors); read before triaging it.
5. `docs/templates/finding.md` — the T1 filing shape.
6. `docs/findings/finding-0026.md` — the warrant chain this work closes.

## 3. Investigation & grounding

- **Q1 — where is the checked-region config?** `pyproject.toml` `[tool.mypy]` block:
  Tier-1 strict components live under `[[tool.mypy.overrides]] module = "core.*"`
  (mypy forbids `strict = true` inside overrides — the components are expanded there).
- **Q2 — what is the error surface?** 193 errors in core (mypy 2.2.0, 2026-07-11 baseline).
  Hotspots: `core/stores/vectorstore.py` (15), `core/stores/telemetry.py` (8),
  `core/sensing.py` (8), `core/sandbox/runner.py` (8), `core/complex/temporal.py` (8),
  `core/ingest/index.py` (7). Dominant kinds repo-wide: `arg-type` 138, `attr-defined` 93,
  `type-arg` 45, `union-attr` 38 — `union-attr` and implicit-Optional shapes are the note's
  canonical T1 candidates (§2.3).
- **Q3 — which third-party boundaries lack stubs?** Measured (V2, 2026-07-11): `lancedb`,
  `sknetwork`, `psutil` ship no `py.typed`; `duckdb`/`numpy`/`scipy`/`cryptography` are typed.
  Interim `ignore_missing_imports` overrides exist in `pyproject.toml` — this plan replaces
  them with wrapper modules per §2.5 (Any quarantined to one file per dependency).
- **Q4 — where do the untyped deps enter core?** `lancedb` → `core/stores/vectorstore.py`;
  `sknetwork` → `core/complex/blocks.py` (Louvain cross-check); `psutil` → the vitals path
  (`core/stores/telemetry.py` / vitals collector). The builder re-confirms exact import
  sites before wrapping — the code, not this list, is authoritative.
- **Q5 — wrapper module location?** The code does not settle this; the note says only
  "thin typed wrapper modules" (§2.5). Default pinned here: `core/typedshims/<dep>.py`
  (new package, core-internal, no re-exports of `Any`). Owner may override at approval.

**Additional risks or questions surfaced during reading:** annotation changes in core
ripple into Tier-2 call sites (tests especially) — expected; Tier-2 remediation is
bp-007's job, and this plan must not chase errors outside `core/`.

## 4. Reconciliation

- `pyproject.toml` `[tool.mypy]` overrides comment ("V2 … interim ignores; §2.5 boundary
  wrappers quarantine these when B-1's build lands") → **cross-ref: extension** — this plan
  IS that landing; the comment is updated to name the shims, not deleted.
- Any T1 whose fix would change committed *behavior* (not just annotations) → **called out
  as a correction and carried by Item 3**, never slipped into an annotation pass.

## 5. Write scope

Prose mirror: `core/**` (annotations, narrowing, the new `core/typedshims/` package),
`pyproject.toml` (tightening the mypy overrides as boundaries get wrapped), new findings,
this plan's dir. **Out of scope:** all other tiers (bp-007), the CI gate (bp-008),
`core/provenance.py` tagging (bp-009), design notes (denylisted), `eval/golden/**`,
behavioral changes not carried by a T1 finding.

## 6. Interfaces pinned inline

Triage taxonomy (§2.3, verbatim discipline):
- **T1 — latent defect** → its own finding, each.
- **T2 — representability finding** — `dict[str, Any]` across a boundary where a
  dataclass/TypedDict belongs; not style.
- **T3 — checker friction** → `# type: ignore[<code>]  # warrant: <reason>` — a bare
  ignore is a grep-detectable violation.

Invariant (§2.1): *for every module M in the checked region: every call site, return,
and assignment in M is consistent with the declared types of its callees, modulo
warranted exemptions recorded per T3.*

Tier-1 strict components currently pinned in `pyproject.toml`:
`disallow_untyped_defs, disallow_incomplete_defs, disallow_untyped_calls,
disallow_any_generics, disallow_untyped_decorators, warn_return_any`.

## 7. Items

### Item 1 — Triage the 193

- **Objective:** every core error classified T1/T2/T3 in a triage table in the journal.
- **Files:** `docs/build-plans/bp-006/journal.md` (table), no code.
- **Acceptance test:** table rows == current core error count; every row carries a class.
- **Falsifier:** §2.2 clause 3 — T1+T2 = 0 ⇒ the audit claim fails; record no-signal in a
  finding and stop for owner review before remediating anything.
- **Invariant(s):** none touched (read-only).
- **Touches stored data?** no  **Parallelizable?** no  **Depends on:** none

### Item 2 — Boundary wrappers

- **Objective:** `core/typedshims/{lancedb,sknetwork,psutil}.py` — typed facades; core
  imports the shim, never the raw module; `ignore_missing_imports` overrides narrowed to
  the shim files only.
- **Files:** `core/typedshims/*`, importing core modules, `pyproject.toml`.
- **Acceptance test:** `grep -rn "import lancedb\|import sknetwork\|import psutil" core/
  --include='*.py' | grep -v typedshims` → empty; ratchet green; mypy error count strictly
  drops.
- **Falsifier:** a shim that re-exports `Any` (checker still silent past the boundary) —
  detected by `disallow_any_explicit` spot-check on the shim files.
- **Invariant(s):** Invariant 2 (no network imports — shims wrap compute libs only);
  import-firewall stays green.
- **Touches stored data?** no  **Parallelizable?** with Item 1  **Depends on:** none

### Item 3 — T1 remediation

- **Objective:** every T1 fixed with its finding filed first (finding documents the
  reachable incorrect behavior; the fix cites it).
- **Files:** affected `core/**`, `docs/findings/finding-00XX.md` per T1.
- **Acceptance test:** per-T1: the finding exists, a regression test or property test
  covers the defect where testable, ratchet green.
- **Falsifier:** a "T1 fix" that changes no behavior under test — reclassify T2/T3 and
  annotate the finding honestly.
- **Invariant(s):** all — behavioral changes only via this item, each warranted.
- **Touches stored data?** no (store *code* may change; migrations stop-and-raise)
  **Parallelizable?** no  **Depends on:** Item 1

### Item 4 — T2/T3 sweep to strict green

- **Objective:** T2 shapes typed (TypedDict/dataclass per the note's open-question
  convention — builder picks ONE and records it), T3s warranted+coded; `core.*` strict
  green.
- **Files:** `core/**`, `pyproject.toml`.
- **Acceptance test:** `uv run mypy` reports 0 errors under `core.*`; zero bare ignores
  (`grep -rn "type: ignore$\|type: ignore " core/ | grep -v "ignore\["` → empty).
- **Falsifier:** green achieved with T3 count dominating (checker friction, not audit
  value) — record the T3/total ratio in the journal; if > 1/3, file a finding against the
  note's clause-3 razor rather than celebrating the green.
- **Invariant(s):** §2.1 invariant now holds for Tier 1.
- **Touches stored data?** no  **Parallelizable?** no  **Depends on:** Items 2, 3

## 8. Math carried explicitly

N/A — no mathematical object implemented (annotations and facades only; the provenance
semilattice tagging is bp-009).

## 9. Non-goals

Tier-2 remediation (bp-007); gate wiring (bp-008); `Authored[T]`/`Derived[T]` tagging
(bp-009); runtime validation (PD-2, parked); any dreamer/retrieval behavior change.

## 10. Stop-and-raise conditions

A T1 whose fix requires a store schema migration (blast-radius surprise — park the item,
file the finding, continue); any fix that would require touching a denylisted surface;
an error whose correct fix contradicts the ratified note (spec-defect finding); T1+T2=0
(Item 1 falsifier — owner review before proceeding).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| T2 shape convention | builder picks TypedDict *or* dataclass in Item 4, uniformly | mixing both (audit loses one shape vocabulary) | note's open question — owner may override at approval |
| shim package location | `core/typedshims/` | vendoring stubs (heavier, drifts) ; inline casts (smears Any) | owner renames at approval if preferred |

## 12. Dependency & ordering summary

Item 1 ∥ Item 2 → Item 3 → Item 4. This plan gates bp-007 (Tier-2 errors shift when core
annotations land), bp-008 (gate needs green), bp-009 (tagging builds on a strict-green
provenance module). No other plan may write `core/**` concurrently.

---
type: design-note
id: dn-type-system-as-core-audit
status: ratified # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-10
updated: 2026-07-10
links:
  - docs/research/security-planes.md # this note supplies the enforcement mechanism its code plane names
  - docs/findings/finding-0026.md # the warrant
supersedes: null
superseded_by: null
warrant: finding-0026
---

# The type system as a core code audit

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.

## 1. Purpose and scope

### 1.1 What this note decides

`security-planes.md` assigns the code plane to types. finding-0026 establishes
that no checker runs. This note decides **what a static type checker is for in
this project, what it proves, where it applies, and how it is wired** — and it
reframes the first strict run over `core/` as an _audit of the core_, whose
error inventory is a measurement, not a chore.

Doctrinally this adds nothing to the three-plane composition. It is a
conservative extension: the mechanism the code plane already assumed.

### 1.2 Out of scope (explicit non-goals)

- **Runtime value validation** (pydantic, beartype). Different layer. Parked,
  PD-2. A well-typed value can still be semantically garbage; types verify shape
  between internal parties and never verify values arriving from outside.
- **A soundness proof.** mypy is not sound and this note does not pretend
  otherwise. Its unsound corners are named in §2.3 (T3) and disciplined, not
  wished away.
- **Performance.** Orthogonal. Owned by the parked Rust/PyO3 record.
- **Ecosystem-wide typing.** Scope is fixed by §2.5, not aspirational.
- **Displacing existing gates.** `ruff`, `ops/import_lint.py`, the F9 quality
  suite, Hypothesis, and the drift suite are untouched. This is a new tier
  beneath them, not a replacement for any.

## 2. Principles / decision

### 2.1 What a green run actually proves

Under Curry–Howard a well-typed program _is_ a proof — of **exactly the
proposition its type expresses, and nothing more**.

```python
def add(a: int, b: int) -> int:
    return a - b        # type-checks. The theorem proven is "ints map to ints".
```

A green run therefore does **not** prove the core was built correctly. It proves
the core satisfies whatever specification has been pushed into its types. The
strength of the proof equals the propositional content of the type grammar,
which splits correctness into two obligations:

1. **code ⊨ type-spec** — owned by the checker. Mechanical, continuous,
   conditional on the T3 discipline below.
2. **type-spec ⊨ intent** — never provable statically. Owned by tests, Track L,
   and the owner.

A second boundary, from gradual typing: the guarantee holds only inside the
**checked region**. Unannotated functions are silently exempt; `Any` is
infectious, so one `Any` at a third-party boundary launders everything
downstream out of the guarantee; `cast` and `# type: ignore` are holes by
construction. A green _non-strict_ run over partially annotated code is close to
meaningless. Strict mode's value is that it converts the first two from silent
to loud (`disallow_untyped_defs` forces annotation or explicit exemption;
`disallow_any_generics` / `warn_return_any` stop `Any` propagating unnoticed).

**Invariant (stated explicitly).** For every module M in the checked region:
every call site, return, and assignment in M is consistent with the declared
types of its callees, modulo warranted exemptions recorded per T3.

### 2.2 Three-clause test (standing razor)

1. **What it measures.** Interface consistency across the checked region.
2. **Assumptions that make it valid.** Annotations present and honest (strict
   forces presence, not honesty); no unwarranted `Any` / `cast` / `ignore`;
   third-party boundaries stubbed or wrapped (V2).
3. **What would show it is not earning its place.** If the first strict pass over
   `core/` yields zero T1 and zero T2 findings and steady-state cost is dominated
   by T3 friction, the **audit** claim of this note fails. Record as no-signal;
   the checker may survive as a regression floor, but §2.1's stronger framing is
   withdrawn.

The engineering consequence of §2.1 is the note's central design move: to make
"type-correct" approximate "invariant-respecting," raise the propositional
content of the types. `int -> int` decorates. `promote(x: Derived[T], cap:
OwnerVerdict) -> Authored[T]` constrains. This is the standing razor —
_formalism must constrain, not decorate_ — applied to annotations themselves. An
annotation earns its place by encoding an invariant whose violation the checker
would catch.

### 2.3 The audit framing, and the triage taxonomy

The first strict run over core is an **audit whose findings are the error
inventory**. Every emitted error triages into exactly one class:

- **T1 — latent defect.** Corresponds to a reachable incorrect behavior.
  Canonical shapes: implicit `Optional` flowing into a non-`Optional` consumer;
  union types consumed without narrowing; signatures mismatched across module
  boundaries that happen to work for today's call sites. **Each T1 is filed as
  its own finding.**
- **T2 — representability finding.** Behaviorally fine, but the types reveal
  untyped shape: `dict[str, Any]` crossing a module boundary where a dataclass or
  TypedDict belongs; event-log rows passed as bare tuples. These are not style.
  **A shape the type system cannot see is a shape the code-plane audit cannot
  defend.** T2 density over core measures how much of the system's real structure
  lives outside the checked region.
- **T3 — checker friction.** A mypy limitation, resolved by `cast` or ignore.
  **Discipline:** every ignore carries an error code and a warrant comment —
  `# type: ignore[arg-type]  # warrant: <reason>` — so that bare ignores are
  grep-detectable violations, enforceable on the gate path exactly as
  `import_lint` enforces its allowlist. T3 count is the cost term in §2.2 clause 3.

### 2.4 Provenance labels as types — the static shadow

Two of the three invariants slated for formal treatment have static shadows
expressible in the type grammar:

- **Label monotonicity.** Tag payloads with authorship class at the type level:
  `Authored[T]` / `Derived[T]` (grain deferred — see Open questions). Then

  ```python
  def promote(x: Derived[T], cap: OwnerVerdict) -> Authored[T]: ...
  ```

  makes _accidental_ promotion a type error at every call site, checked on every
  builder run, at zero runtime cost.

- **Capability non-amplification.** Capabilities as unforgeable parameter types:
  a privileged operation whose signature demands the capability object cannot be
  called from a path that never received one. The checker verifies the plumbing
  end to end.

The shadow is **strictly weaker** than the invariant: it sees no values and no
runtime paths, and a deliberate `cast` defeats it. What it removes is the
_accidental_-violation class, at authorship time. That is the aligned move under
the standing principle — the correct design removes the error class rather than
detecting instances of it. The formal treatment retains the full invariant; the
types own the everyday path.

This is precisely the promotion `ops/import_lint.py` already performs for I2:
a runtime guarantee lifted to a static one, provable by reading the AST without
running the program. The type checker generalizes that move.

### 2.5 Scope — the two-tier checked region

The scoping rule is the owner's: **a caller must respect the callee's types.**
mypy verifies call sites in the _caller's_ module, so the rule is enforceable
only if every caller of core is itself analyzed. Hence:

- **Tier 1 — `core/` + the foundation file set.** Full strict. (Synergy with
  B-7: files the builder may never write are exactly the files whose interfaces
  most deserve machine checking.)
- **Tier 2 — the interface tier.** Every module that imports anything from
  `core/`. Membership is not a judgment call but a **mechanical invariant** —
  `imports core ⇒ present in Tier-2 config` — decidable from the AST import graph
  and enforceable on the gate path. Tier-2 flags need not be full strict; the
  load-bearing requirement is that arguments flowing into core calls are not
  `Any` (floor and ceiling in Open questions).
- **Tier 3 — everything else** (no core imports). Unchecked, as a **recorded
  default, not deferred debt.**

Ratchet: no module ever moves to a weaker tier. Tier-2 membership grows
automatically with the import graph rather than by intention.

**Zone interaction (V1a).** `ops/import_lint.py` establishes that `core/` may not
import `edge` or `cloud`, and its docstring records that core↔edge is a
filesystem handoff, never an import. The _inbound_ direction is what Tier 2
concerns, and it is not established by that lint: which of `agents/`, `config/`,
`eval/`, `ops/`, `scheduler/`, `scripts/`, `tests/` import `core` is unmeasured
here. Tier 2 may be small. Its size is an empirical question, not an assumption
this note is entitled to make.

**Residual gaps after Tier 2.** (a) `Any` laundering _inside_ Tier 2 if its flag
subset is too weak — bounded by the flag decision. (b) Dynamic dispatch
(`getattr`, reflection), which no static tier sees. (c) External values at the
ingestion boundary — untouched by any tier, and the standing reason PD-2 exists.

**Boundary wrappers.** Third-party surfaces with poor stubs (V2) get thin typed
wrapper modules, so `Any` is quarantined at one file per dependency rather than
smeared through core. Candidates from `pyproject.toml` runtime deps: `duckdb`,
`lancedb`, `scikit-network`, `psutil`. (`numpy` and `scipy` ship or have
maintained stubs; `cryptography` is typed.)

### 2.6 Enforcement wiring

A config nothing invokes enforces nothing. Default recorded, PD-1:

- **Default: `mp-finish` pre-merge.** Worktree isolation means every build lands
  through `mp-finish`; a check there guarantees no unchecked code reaches the
  mainline, and the cost is paid once per merge rather than per keystroke.
- **Rejected-with-record:** Stop-gate hook (faster feedback; pays the cost at
  every session stop). CI (`.gitlab-ci.yml` currently declares only `sast`,
  `secret_detection`, and semantic-release, plus two `pipeline-fragments`
  includes not read — V4; if the fragments already run pytest, CI becomes a
  live option).

## 3. Consequences

### 3.1 What this note licenses

A build plan implementing V-items and B-items below, scoped to `pyproject.toml`,
a Tier-2 config, wrapper modules, and — for B-3 only — `core/provenance.py`.
It licenses no change to the three-plane composition itself.

### 3.2 Verification items

- **V1.** _(Resolved 2026-07-10, in-session.)_ No mypy config exists anywhere in
  the tree; no checker is in the `dev` extra; no gate path invokes one. Evidence
  in finding-0026.
- **V1a.** Which top-level packages import `core/`? Determines the true size of
  Tier 2. Answerable by extending the AST walk in `ops/import_lint.py`.
- **V2.** Stub availability and quality for `duckdb`, `lancedb`,
  `scikit-network`, `psutil` (`sqlite3` is stdlib-typed). Determines wrapper
  scope per §2.5.
- **V3.** Baseline measurement: first strict run over Tier 1 in report-only mode;
  error count by module, triaged per §2.3.
- **V4.** Whether the `pipeline-fragments` includes in `.gitlab-ci.yml` already
  run `pytest` / `ruff`. Establishes whether CI is a live alternative for PD-1.

### 3.3 Builder items

Ids are note-local; renumber into the global B-series at ratification.

- **B-1 — the audit.** In a worktree: add mypy to the `dev` extra, configure
  strict over Tier 1 and the interim flag floor over Tier 2, run report-only.
  Produce a T1/T2/T3 inventory with path-and-line for every error. File each T1
  as its own finding.
  _Falsifier:_ §2.2 clause 3 — if T1 + T2 = 0, the audit claim fails and is
  recorded as no-signal.

- **B-2 — wire the gate.** Once both tiers are green, add the check per PD-1,
  **including the Tier-2 membership invariant** (import-graph scan asserting
  `imports core ⇒ in Tier-2 config`), and the bare-ignore scan from §2.3 T3.
  _Falsifiers, all three must hold:_ (i) an injected type error in a scratch
  commit blocks `mp-finish`; (ii) a scratch module importing `core` but absent
  from Tier-2 config blocks; (iii) a bare `# type: ignore` with no error code
  blocks.

- **B-3 — static-shadow spike.** Express `Authored` / `Derived` tagging in
  `core/provenance.py` per §2.4; measure churn.
  _Falsifier:_ if tagging requires warranted ignores at more than a handful of
  sites, the static-shadow claim is weakened; park the spike with that evidence
  attached rather than forcing the encoding.

## Parked decisions

| id   | decision                                       | default recorded                                              | re-entry condition                                                                                                                                                                                                                                                                          |
| ---- | ---------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PD-1 | gate location                                  | `mp-finish` pre-merge                                         | V4 shows CI fragments already run pytest; **or** B-1 measures a steady-state check runtime that makes per-merge cost material                                                                                                                                                               |
| PD-2 | runtime validation layer (pydantic / beartype) | none                                                          | T1 defects cluster at the ingestion boundary, where static types cannot reach                                                                                                                                                                                                               |
| PD-3 | checker identity                               | mypy (pyright rejected-with-record)                           | a _measured_ gate-path runtime problem, not an anticipated one                                                                                                                                                                                                                              |
| PD-4 | relation to the Rust/PyO3 split                | unchanged; this note is the cheap experiment on the same axis | B-1 outcome feeds the split's re-entry: if strict typing plus wrappers closes the T1 class on privileged paths, the split's **security** motivation weakens to performance-only; if T1 defects persist in shapes Python's grammar cannot express, that is concrete evidence _for_ the split |

## Open questions

- **Tier-2 flag floor.** What is the minimal flag subset preventing `Any`
  arguments from reaching core call sites? Candidate floor:
  `check_untyped_defs` + `disallow_any_generics`; full strict is the ceiling.
  Decide from B-1 evidence, not a priori.
- **Tagging grain (§2.4).** Does the four-class authorship-distance axis belong
  in the type tags, or is the binary `Authored` / `Derived` shadow the right
  grain for a checker? The four-class axis is ordered; the type grammar is not.
- **Tagging depth.** Values only, or containers of tagged values? Variance gets
  sharp quickly.
- **T2 convention.** TypedDict or dataclass for event-log row shapes surfaced as
  T2 — chosen once, applied uniformly.

## Cross-references

Verified in-session, 2026-07-10:

- `pyproject.toml` — `[project.optional-dependencies].dev` = pytest, ruff,
  hypothesis; no `[tool.mypy]`; `[tool.ruff.lint].select = ["E","F","I","B","UP"]`.
- `ops/import_lint.py` — AST import-graph firewall; module docstring states the
  static-tier promotion argument for I2; asserted in `tests/test_import_firewall.py`.
- `.gitlab-ci.yml` — `sast`, `secret_detection`, semantic-release; two
  `pipeline-fragments` includes unread (V4).
- Recursive glob `**/mypy*` over the repo (excluding `.venv`, `.git`, `.jj`,
  `node_modules`) — no matches.

Asserted from the design record, not re-verified here:

- `docs/research/security-planes.md` — three-plane composition; the code plane
  and its TLA+/Alloy + Hypothesis invariant list.
- `docs/design-notes/authorship-distance-axis.md` — B-7 (sole-write-path audit),
  the four-class axis referenced in Open questions.
- The parked Rust/PyO3 privileged-path record — PD-4.

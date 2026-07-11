---
type: design-note
id: dn-code-observation-projection
status: ratified # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only # nothing built; the ledger precursor exists, the projection does not
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/brainstorms/doc-code-entanglement.md # the two warrant capsules
  - docs/brainstorms/code-as-sensor-stream.md # the stream-classification ruling this finalizes
  - docs/design-notes/authorship-distance-axis.md # §3.7 interpreter formalism; a₂ cross-map
  - docs/design-notes/the-edge-model.md # §2 deterministic ingest lays fibers; E_geom ⊔ E_disp
  - docs/design-notes/observed-data-and-the-assistant-tier.md # the firewall this must not weaken
  - docs/design-notes/observed-iot-and-cross-source-synthesis.md # correlator safety rules (§2)
  - docs/findings/finding-0021.md # code as corroboration arbiter — the value, evidenced
supersedes: null
superseded_by: null
warrant: docs/brainstorms/doc-code-entanglement.md
---

# The code-observation projection — φ_code into the observed stratum

> Composed by the orchestrator at the owner's instruction (2026-07-11); placed and
> ratified by the owner's hand. `/graduate` refuses this note until `status: ratified`.

## 1. Purpose and scope

### 1.1 What this note decides

Code, comments, and documentation are **not** authored-dialogue corpus (owner ruling,
2026-07-11). They are a sensed stream — the repo is an instrument, the code sensor is its
interpreter. This note decides **how that stream is projected into the corpus**: the
observation schema, the entry seam, which stratum receives it, the two-lane consumer
split that lets code semantics _detangle_ threads in the strata, and the firewall
obligations that make all of it safe. It finalizes the interaction the
code-as-sensor-stream ruling left at "event-log-only, pending design."

The one-sentence architecture: **the code sensor becomes a projection mapping
(φ_code, the axis note's §3.7 interpreter shape) from the repo into the observed
stratum, and code meaning reaches the rest of the strata only through two typed lanes —
deterministic reference edges and correlator-class interpreted proposals.**

### 1.2 Out of scope (explicit non-goals)

- **The smear** (multi-scale chunk embedding) — parked with re-entry in the warrant
  capsule; collides with the standing single-scale decision and needs measured evidence.
- **The docstring format standard** — parked; re-enters if extraction quality proves
  gated on form (V4 below measures this).
- **The correlator/detangler itself** — Track D builds the consumer; this note builds
  the substrate it reads.
- **Any promotion path for code observations.** Observations never become authored —
  not by verdict, not by anything. Code is builder-produced reality, not owner belief
  (finding-0021); there is nothing to promote _to_. This is stronger than the I1
  verdict-gate: the path does not exist.
- **Ingesting code TEXT into the vector corpus.** The projection carries structure and
  prose-about-code (docstrings, references), not source bodies. Re-entry only via a
  ratified amendment with a measured retrieval case.

## 2. Principles / decision

### 2.1 Stream classification (settled, restated as the foundation)

Per the owner rulings of 2026-07-11: the repo is an instrument; commits are its
readings; the code sensor is the sole interpreter; **no new provenance class** — under
the current enum the projection lands as `OBSERVED`; under the authorship-distance axis
(when ratified) it maps to **a₂ (author-sensed)**. The a₂ cross-map is recorded here so
the axis ratification re-labels without re-designing. Never `AUTHORED_*` (masquerade at
origin: builder output entering the self-model), never `AUTHORED_DIALOGUE` specifically
(dialogue is MIRROR_READABLE — the exact leak), never `CURATED` (docs-as-testimony would
erase the testimony-vs-measurement distinction the archive pass depended on), never
`INTERPRETED` (observations are measurements, not system inferences over the corpus).

### 2.2 φ_code — the interpreter contract

The projection satisfies the axis note's §3.7 interpreter shape, and must keep doing so:

- **Deterministic**: AST + git facts only; no model in the loop. Re-running φ_code over
  the same commit yields identical observations (content-addressable, testable).
- **Sole path in**: code observations enter the observed stratum through φ_code and the
  handoff seam only — never through vault sync, never through dialogue capture.
- **Transform-attributed**: each observation batch carries the interpreter's identity
  (the code sensor attests already: `code_sensor / ingest_commit`; the projection adds
  `code_sensor / project_observations` with the commit sha as input, chained).
- **Versioned re-interpretation**: a φ_code upgrade (better reference extraction) is a
  re-projection — new observation rows superseding old at the same (commit, symbol) key,
  never an in-place mutation. The ledger's blob-identity makes this cheap.

### 2.3 The observation schema

One observation = one symbol-grain reading of one commit:

```
CodeObservation:
  commit_sha      str     # the reading's time coordinate (git's own content address)
  path            str     # file within the tree
  qualname        str     # symbol (module-level = "")
  kind            str     # module | class | function | async_function
  signature       str     # unparsed arg list ('' for classes/modules)
  docstring       str     # the Rosetta payload — verbatim, '' if absent
  references_out  list    # typed: [{type: note-citation | path-mention | symbol-mention
                          #          | design-ref, target: str, source_line: int}]
  provenance      OBSERVED (structural; the store writes nothing else — DerivedStore pattern)
```

Grain default: **symbol** (module row for module docstrings). The docstring is carried
verbatim because it is the _state transition between English and code_ (owner framing):
the one layer of the stream already written in corpus-language. References are extracted
deterministically: explicit paths, `design-notes/*.md` citations, `[[note]]` links,
backticked symbol mentions — patterns V4 verifies before anything is trusted.

### 2.4 The seam — how observations enter

The existing sensing pattern, unchanged in shape: the sensor (ops tier, unsealed — the
restic precedent) writes an observation batch to the **filesystem handoff**; core
collects through the `SensingHandoff`-family seam into a dedicated
**`code_observations` store** (its own table — not `sensor_readings`, which is the
biometric contract; same store _family_, same constructor discipline: the store writes
OBSERVED and nothing else, `DerivedStore.add`-style, no provenance parameter to lie
with). `ObservedView`-compatible: the observed-only constructor check applies as-is.
Cadence: per main-merge (riding the existing post-commit sync), idempotent by
(commit_sha, path, qualname) — a missed batch heals on the next sync, rescan-style.
V1 verifies the seam signatures at source before any build.

### 2.5 The two lanes — how code meaning reaches the strata (the load-bearing split)

**Lane 1 — deterministic references → typed cross-stratum reference edges.**
A docstring citing `recursive-strata.md`, a design note naming `core/recursion.py` —
observer-independent facts, extractable without judgment: geometry-class authority per
the edge model's §2 ownership rule. **But they are cross-stratum** (observed-node ↔
authored/curated-node), and the mirror's reasoning complex 𝔎|\_MR is authored-only — so
these edges must NOT enter `A_geom` uninvited. Decision: they live in a dedicated
**reference-edge store** the balance math holds no handle to (the E_disp separation
pattern applied to a geometry-authority store: separated not because the edges carry
intent, but because their endpoints cross strata). `build_complex`'s signature stays
untouched. Consumers: the detangling instruments and (when it unparks) Item 10's
`s(C,D)` external-corroboration feature — finding-0021's manual arbitration, structural.

**Lane 2 — semantic disambiguation → correlator-class interpreted proposals.**
"This code's behavior supports thread A's reading over thread B's" is judgment. It runs
in the correlator family under the observed-iot §2 safety rules verbatim: reads
observed + interpreted only, never raw authored text; outputs INTERPRETED proposals
only; writes nothing authored; dreamer-proposed authority; anything touching blessed
content routes through the (Item 8) blessing gate. Lane 2 is licensed by this note but
**built only after Lane 1 exists** — proposals need the reference substrate to cite.

The lanes never merge. A reference is never upgraded to a semantic claim by virtue of
existing; a semantic proposal is never laundered into geometry authority.

### 2.6 Firewall obligations (what this must never weaken)

- `MIRROR_READABLE` untouched: code observations are structurally mirror-opaque; the
  self-model never reads them. The Dreamer's introspective path is unchanged.
- The observed-data core decision stands: no shared pool for the self-model, no silent
  promotion, raw-exhaust reasoning prohibitions — all inherited verbatim.
- The sealed core touches no network: φ_code runs ops-side; core only collects from the
  handoff, exactly as the sensing seam already prescribes.
- Under the axis note's ratification, Lane-2 readability is re-derived from its declared
  class-set machinery (§5.1); nothing here pre-empts that — the a₂ cross-map is the join.

### 2.7 Three-clause razor (what this earns, when it fails)

1. **Measures:** whether code semantics can disambiguate corpus threads — the
   entanglement made structural.
2. **Valid when:** references are extracted deterministically and completely enough that
   Lane 1's edge set is high-precision (V4); the firewall obligations hold structurally.
3. **Fails its keep if:** the reference inventory over the real corpus is near-empty or
   noise-dominated (V4 falsifier), or a built detangler adds no measurable
   discrimination to thread separation that cosine + fibers alone achieve. Record as
   no-signal; the ledger remains valuable independently.

## 3. Consequences

### 3.1 What this note licenses

On ratification: a build-plan family scoped to the observation store + seam, the sensor
projection, the ledger docstring column, and the Lane-1 reference-edge store. It
licenses **no** correlator build (Track D's plan), no mirror change, no promotion
machinery, no code-text embedding.

### 3.2 Verification items (grounded pass before any build)

- **V1** — seam signatures at source: `SensedObservation` / `SensingHandoff.collect` /
  `ObservedView` constructor semantics (`core/sensing.py`) — confirm the projection can
  ride them or name exactly what a `code_observations` sibling needs.
- **V2** — store family: confirm the DuckDB-vs-SQLite choice for `code_observations`
  against CONVENTIONS §Data stores (telemetry/time-series → DuckDB; ledgers → SQLite;
  observations are append-only readings keyed by commit — arguable both ways; decide
  with citations, record rejected alternative).
- **V3** — the ledger precursor: docstring extraction column in `code_snapshots.sqlite`
  (the AST walk already visits every def — measure the delta cost, expected trivial).
- **V4** — **the reference inventory (the feasibility probe, read-only, can run before
  ratification)**: walk current docstrings + design notes for cross-references; report
  edge count, precision on a hand-checked sample, and whether extraction quality is
  gated on docstring form (feeds the parked format standard).

### 3.3 Builder items (post-ratification, blast-radius ordered)

- **B-a** — ledger docstring column + doc-coverage metric (additive migration; the
  evolution study gains a documentation axis). _Falsifier: extraction misses docstrings
  the AST exposes._
- **B-b** — `code_observations` store + handoff collection + `project_observations`
  attestation; idempotent per commit. _Falsifier: a second projection of the same commit
  changes row count._
- **B-c** — Lane-1 reference-edge store + φ_code extraction, seeded by V4's validated
  patterns; balance-math isolation proven by the bit-identical-instruments test pattern
  (`test_edge_partition.py` precedent). _Falsifier: any instrument result changes when
  reference edges are added or removed._
- **B-d** _(gated on Track D or a dedicated plan)_ — the first detangling consumer.

## 4. Parked decisions

| id   | decision                                                                            | default recorded                              | re-entry condition                                                                              |
| ---- | ----------------------------------------------------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| PD-a | observation grain                                                                   | symbol-level                                  | V4 shows references resolve mostly at file level (grain too fine) or chunk level (too coarse)   |
| PD-b | code-text embedding                                                                 | never (structure + docstrings only)           | a measured retrieval case where docstring+reference retrieval fails but body-text would succeed |
| PD-c | docstring format standard                                                           | CONVENTIONS "comment the why" only            | V4 shows extraction quality gated on form                                                       |
| PD-d | historical backfill of observations (all 130+ commits) vs from-ratification-forward | backfill (the ledger already proves it cheap) | projection cost measured non-trivial at V3                                                      |

## 5. Open questions

- **OwnerVerdict interaction**: Lane-2 proposals that would re-rank or demote anything
  blessed need the verdict machinery — does the detangler wait on the verdict taxonomy
  (finding-0028's riders), or operate proposal-only forever? (Default: proposal-only.)
- **Reference-edge symmetry**: a note→code edge and its code→note mirror — one edge or
  two? (Bears on Lane-1 store schema; V1 territory.)
- **Does the observed-stratum spike's supersession** (pending, axis §8) change any of
  §2.6? Expected no — this note reads the firewall as the axis preserves it — but the
  ratification orders should be checked at the gate.

## Cross-references

Verified in-session 2026-07-11: `core/sensing.py` (SensedObservation/ObservedView/
SensingHandoff exist, constructor-enforced observed-only); `core/provenance.py`
(MIRROR_READABLE frozenset; OBSERVED mirror-opaque; Authored[T]/Derived[T] tags live as
of bp-009); `ops/code_snapshot.py` (AST walk per commit, 134+ snapshots); zero E_geom
fiber writers exist (2026-07-10 survey). Asserted from the design record:
the-edge-model §2/§4; observed-iot §2; authorship-distance-axis §3.7/§5.

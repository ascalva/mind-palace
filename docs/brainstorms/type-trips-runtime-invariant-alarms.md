# type-trips-runtime-invariant-alarms

## 2026-07-26T00:00:00Z

```capsule
topic: type-trips-runtime-invariant-alarms
date: 2026-07-26

seed: |
  Owner, verbatim: "the development side of this project can rely on core-type code, mypy checks,
  but the types can still be disobeyed (even if by accident), but that's a trip, a system trip, that
  the parent class for the type enforces with a trip (when I say trip, I'm thinking of someone
  tripping on a laser motion detection system, an alarm)."

⚑ the observation is correct and the repo already has the evidence: |
  mypy is STATIC and OPT-IN, and this repo knows it — there is a **69-error tests baseline**, an
  `ops.type_gate` bolted on beside mypy to catch what mypy structurally cannot (bare ignores,
  tier-2 membership, raw shimmed imports), and a separate `scripts/check_imports.py` walker. Three
  tools because one static checker was never enough.

  Every one of these bypasses mypy entirely, at runtime, silently:
    `# type: ignore`  ·  `Any`  ·  `cast()`  ·  untyped call sites  ·  **data crossing a boundary**
  The last is the big one here: TOML config, SQLite rows, JSON over the worker pipe, embedder
  output. `dict[str, Any]` from a store read is a type annotation making a PROMISE that nothing
  checks. bp-110's `Batch.rows` is literally `tuple[dict[str, Any], ...]`.

the idea, restated: |
  A parent class carries the invariant. When an instance is constructed that violates it, the
  construction TRIPS — a laser-alarm, not a lock. The value is in the NOTICING.

⚑⚑ THE DESIGN QUESTION THAT DECIDES EVERYTHING — does a trip RAISE or OBSERVE?
  - **RAISE (fail-closed)** — correct for SAFETY invariants: the sealed core, the memory ceiling,
    the worker holding no store. These already raise (`MemoryCeilingError`, `assert_sealed`), and
    turning a violation into an outage is the RIGHT trade when the alternative is a breach.
  - **OBSERVE (fail-loud, continue)** — correct for HYGIENE invariants. This is what the owner's
    metaphor actually describes: a motion detector does not lock the door, it tells you someone
    walked through.
  ⇒ The taxonomy of which invariant is which IS the design work. Getting it backwards is expensive
  in both directions: a hygiene trip that raises converts a cosmetic bug into a daemon outage under
  launchd KeepAlive; a safety trip that merely observes is a breach with a log line.

⚑ THE FAILURE MODE, and this repo has been burned by it three times already: |
  **An alarm nobody reads is a note, and a note is not a control** (finding-0222). A trip that
  writes to stderr is decoration. Its value is ENTIRELY in its consumer.
  ⚑ But the consumer already exists: every commit in this repo prints
  `self-sensor sync: projected=N observation_rows=N warnings=N` — there IS a live observation lane
  ingesting things the system notices about itself. A type trip's natural output is an OBSERVATION
  routed there, not a log. That also makes it a self-map datum, which is the project's own framing.
  Precedent for the failure it avoids: finding-0011 (built but unwired ⇒ a claim, not a mechanism)
  and finding-0223 (a scan that REPORTS but whose exit-code vote was parked — deliberately, and it
  still names the violation, which is exactly the observe-don't-raise pattern working).

open_questions:
  - ⚑ COST. Runtime validation on hot paths is not free: 302,010 queue rows, 2560-dim vectors,
    per-batch landing measured at p50 16.55 ms for 500 rows (bp-110 V1). A per-row trip could
    dominate that. Options: validate at BOUNDARIES only (store read, pipe deserialize, config load)
    rather than per object · sample · or make it a debug-mode gauge. Boundary-only is probably right
    — the boundary is exactly where the `Any` enters.
  - ⚑ `assert` IS NOT A TRIP. It vanishes under `python -O`. Trips must raise explicitly or record
    explicitly; an assert-based alarm is one interpreter flag from silence.
  - What is the parent-class mechanism? `__post_init__` on the frozen dataclasses the repo already
    uses everywhere · `__init_subclass__` to force subclasses to DECLARE their invariant ·
    descriptors. `__init_subclass__` is interesting because it makes "you forgot to state your
    invariant" itself a trip — a violation of the meta-rule.
  - Does the trip fire in TESTS only, or in production? If tests only, it is a fancier assert and
    catches nothing at 3am. If production, see the raise/observe split above.
  - Relationship to the existing three checkers — is this a FOURTH tool, or does it subsume the
    runtime half that `ops.type_gate` cannot reach? A fourth tool needs a reason not to be folded in
    (owner's DRY strictness: duplicated mechanism is a defect, not a nit).
  - ⚑ Does a trip that fires become a FINDING automatically? That would close the loop from runtime
    violation → artifact chain, which is the only path back into design. But an auto-filed finding
    on a hot path is a finding flood; needs dedup/rate-limit, i.e. the same "first seen" shape the
    email-probe lane needs.

connections:
  - `docs/design-notes/type-system-as-core-audit.md` — the ratified frame this extends
  - finding-0222 (a note is not a control) · finding-0011 (built ≠ wired) · finding-0223
  - The owner's standing principle: a property is only real when a test or ratchet PROVES it;
    build the enforcement, do not trust convention.

next_steps:
  - Hold as a brainstorm. It is a genuine third leg beside static typing and the import firewall,
    but it should be designed AFTER the role-state note lands — both touch what the system records
    about itself, and the observation lane is the shared seam.
```

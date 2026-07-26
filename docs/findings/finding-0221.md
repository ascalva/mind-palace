---
type: finding
id: finding-0221
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/build-plans/bp-095/plan.md
  - docs/build-plans/bp-093/journal.md
  - docs/build-plans/bp-094/journal.md
  - docs/design-notes/code-ingest-pipeline.md
ftype: blocker
origin_plan: bp-095
route: orchestrator
resolution: null
---

# bp-095's M-C4 gate is UNREAD (not degenerate) — and both S↔F populations are provably empty, so the gate needs a second clause

## What

bp-095 (CI-4, the S↔F code↔design lens) was opened for build and **refused at its own
§10 stop-and-raise**. The gate worked exactly as designed; this finding records the
disposition of the one state its `re_entry` never contemplated.

**1. The gate is unread, which is a third state.** bp-095's front-matter `re_entry` reads
*"M-C4 verdict = informative (bp-093 journal) — if degenerate, this plan is superseded by a
finding, never built"*, and §10 reads *"The M-C4 gate unread or degenerate (do not start;
flip per `re_entry`)."* The verdict in bp-093's journal is neither:

- `docs/build-plans/bp-093/journal.md:70` — heading: **"M-C3 / M-C4 REAL verdicts — PARKED
  (re-entry: the owner-visible seed run)."** Line 76: *"A degenerate M-C4 is a FINDING with
  the embedder-bump re-entry (PD-C), never a silent tune."*
- The only string `INFORMATIVE` in that journal (line 63) is a **unit-test case name**
  (`M-C4 INFORMATIVE (classes share the space) vs DEGENERATE (orthogonal subspaces,
  cross_median<0.05)`) over the deterministic **fake** embedders — a synthetic assertion
  that the verdict logic discriminates, not a reading of the real corpus.

So the gate is **UNREAD**. `re_entry` prescribes an action for `informative` (build) and for
`degenerate` (supersede on a finding), but the plan can be flipped `superseded` **only** on a
degenerate reading. Asserting `superseded` here would fabricate a negative verdict out of an
absent one — a null reported as a result. The plan is therefore left `ready`, un-started, and
this finding is its recorded disposition. Nothing in `write_scope` was created
(`eval/code_sf_lens.py` and `tests/unit/test_code_sf*` do not exist; no partial work).

This is already the orchestrator's own recorded expectation — `docs/PROGRESS.md:5379`:
*"CI wave sealed through CI-3 (bp-092/093/094); **bp-095 (CI-4) is GATED, not built**."*

**2. The new information: BOTH halves of the join are provably empty, not merely thin.**
The lens is a join of an S-population (code↔note cosines) against an F-population (resolved
code↔corpus reference edges). Measured on this machine today, both are empty at the source:

| Population | Evidence | State |
|---|---|---|
| S — code vectors | no LanceDB/vectorstore directory exists anywhere under `~/.mind-palace/` (only `vault/`, `exhaust/`, and three 0-byte sqlite files) | **empty — corpus never seeded** (bp-092 parked the seed run) |
| F — resolved code↔corpus edges | `~/.mind-palace/reference_edges.sqlite` is **0 bytes**; `ops/code_sensor.py:154` `ENABLED_L2B_PATTERNS: frozenset[str] = frozenset()` (*"empty = all off"*) | **empty — patterns ship DISABLED**, bp-094 Item 2 (the M-C6 enable) parked on owner/deskcheck |

bp-095 §3 predicted *"an empty/thin first read is LIKELY."* It is not likely — at present it is
**certain**, and certain for two independent reasons, only one of which the gate encodes.

## Why it matters

**For a `blocker`: why this session cannot proceed.** bp-095 is a *single-item* plan — Item 1
is the entire plan. There is no sibling criterion to park-and-continue past (§5), and §10's
instruction is the unambiguous *"do not start."* So the session ends without building, per
CLAUDE.md's rule that only a `blocker` does so.

**The substantive consequence — the gate is under-specified by one clause.** bp-095 §6 pins an
**honest-seam law**: *"zero claims when either population is empty; silence never narrated as
structure."* Combined with the table above, a lens built and run today would be **correct and
would emit exactly zero claims** — by its own law. That is worse than useless, it is
unfalsifiable: §7's acceptance test ("every emitted claim carries its witness tuple") would
pass vacuously on an empty set, and §8's keep-condition cannot even be evaluated, because §8
states the reading is *"valid when: one embedder version; **F-population non-trivial**; σ
pinned"* and *"fails its keep if readings are all-null across cuts **once F-edges exist in
volume**."*

So the plan's own §8 already knows a non-trivial F-population is a validity precondition —
but the front-matter `re_entry` gate encodes **only** the M-C4 clause. An informative M-C4
alone is therefore *not sufficient* to license this build: M-C4 is a geometry reading over
code and note **vectors**, and would go green on a seeded corpus while the F-edge population
was still zero (patterns off / Item 2 parked). That is a live, reachable false-green: the gate
would open, the lens would build, every test would pass, and the instrument would be
machinery-ahead-of-need that no reading ever exercised — precisely the "built but never
validated" failure the project treats as a defect.

**Recommendation (owner/orchestrator ruling, not taken here).** Before bp-095 starts, widen
its `re_entry` to a conjunction, promoting §8's existing validity condition into the gate:

> M-C4 verdict = informative **AND** the resolved code↔corpus F-edge population is
> non-trivial (bp-094 Item 2 enabled per M-C6, a projection/backfill run, count > 0 and
> reported) — else the lens parks as vocabulary per §8, on a finding.

This is a gate-completeness change to a plan's front matter, so it is the orchestrator's to
make (a plan edit, and `proposed→ready` re-blessing is owner-only) — not a builder's.

## Re-entry condition

bp-095 stays `ready` and un-started until **all three** hold:

1. The owner-visible CI-1 seed run happens (the code-ingest deskcheck: one idle daemon run
   with Ollama — `docs/PROGRESS.md:5382-5385`, already the track's named deskcheck subject).
   `qwen3-embedding:4b` **is** present locally and Ollama **is** reachable, so the blocker is
   the owner-owed act, not the tooling.
2. `run_mc4(store)` is run on that seeded store and its verdict **recorded in bp-093's
   journal** as a real reading — `informative` opens this gate; `degenerate` fires F-CI4 and
   flips bp-095 `superseded` per its `re_entry` (never a silent tune; PD-C embedder-bump
   re-entry).
3. The F-population is non-trivial and its count reported (bp-094 Item 2 enabled per M-C6 +
   a projection run) — *pending the ruling above; if declined, this clause drops and bp-095
   proceeds on M-C4 alone with an all-null first read expected and sealed as such.*

Why the builder did **not** simply open the gate itself, though the embedder was available:
seeding the real corpus is a **large mutation of stored data**, and bp-095 is a *read-only*
survey ("Touches stored data? **no**"; §5 "read-only against every store") whose `write_scope`
is `eval/**` only; enabling `ENABLED_L2B_PATTERNS` is bp-094 Item 2's owner-gated M-C6 act;
and the seed run is explicitly owner-owed and deskcheck-reserved (`docs/PROGRESS.md:5408-5411`).
Performing any of the three would have breached scope to manufacture the signal that licenses
the build — the exact inversion §9 forbids ("No thresholds tuned to manufacture signal").

## Routing

`blocker` + `direction` → **orchestrator**. Two decisions, neither a builder's:

1. **Gate completeness** (the recommendation above) — widen bp-095's `re_entry` to require a
   non-trivial F-population alongside an informative M-C4, promoting §8's validity condition
   into the gate. Batch to `owner-questions.md` if the owner's call is wanted; the
   `default_if_unanswered` degrades to exactly the parked state above, so nothing stalls.
2. **Confirm the disposition** — bp-095 left `ready` (not `in-progress`, not `superseded`,
   not `complete`), since `superseded` is licensed only by a degenerate reading.

No spec-defect against `dn-code-ingest-pipeline`: the note's §3 CI-4 entry (*"conditional on
CI-1 + CI-3 landing and M-C4 showing signal"*) and F-CI4 (line 620) are self-consistent and
the double gate did its job. The gap is narrowly in bp-095's front-matter `re_entry`, which
encodes one of the two validity conditions its own §8 names.

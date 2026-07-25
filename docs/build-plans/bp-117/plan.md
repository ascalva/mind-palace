---
type: build-plan
id: bp-117
track: ops
status: proposed
design_ref:
  - docs/design-notes/dn-local-model-runtime.md
contract: builder
write_scope:
  - eval/runtime_equivalence.py
  - tests/unit/test_runtime_equivalence.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: [bp-116]
parallelizable_with: []
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/brainstorms/local-model-runtime.md
  - docs/findings/finding-0174.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/brainstorms/local-model-runtime.md
---

# Build Plan — P3: the equivalence gate (the owner-ruled cutover precondition)

## 0. Mode & provenance

**P3 of `dn-local-model-runtime` §2.6**, built to §2.5's specification. Its authority is an
**owner ruling**, 2026-07-25, verbatim: *"I agree with the non-goal of swapping models, first we
need to make sure the same model produces the same results as our baseline."*

⚑ **This is a CUTOVER GATE, not a report.** Nothing in bp-118 or bp-119 may proceed until this
harness exists and passes. The hazard it exists to prevent, named in §2.5: a partial or unvalidated
cutover leaves `data/vectors.lance` holding vectors from **two runtimes**; every cosine across that
boundary is then subtly wrong and **nothing detects it** — not the drift gauge, not `status`, not
any ratchet. The first symptom is bad retrieval months later, on the one asset that cannot be
rebuilt from git.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.

## 1. Objective

A runnable harness proves, to a measured tolerance, that the same model under the new runtime
produces the same embeddings and the same retrieval as the blessed baseline.

### 1.2 Non-goals (explicit — see §9)

Not the cutover itself (bp-118). Not a model change (owner-stated). Not a production monitor —
§2.5 is explicit that this is a **tier-4 ratchet**, a property proven at a point in time, and it
must not be described as anything more.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-local-model-runtime.md` — **§2.5 in full** (the hazard, the position, the
   tolerance, the three-part harness spec), **§2.1 F** (the measured cross-runtime numbers),
   §2.9's equivalence falsifier — the content spec
2. `docs/brainstorms/local-model-runtime.md` — the owner's equivalence capsule; the ruling verbatim
3. `eval/golden.py` — **whole file, 132 lines. READ AND RUN, NEVER WRITE** (foundation denylist)
4. `eval/golden/` — the frozen corpus, queries and blessed baseline. **Same rule.**
5. `docs/build-plans/bp-116/plan.md` §6 — the manager, which this harness uses to spawn a server
6. `docs/build-plans/bp-115/plan.md` §6 — the `InferenceClient` protocol both backends satisfy
7. `config/defaults.toml:265-290` — the σ-thresholded instruments this tolerance protects

⚑ **Does core already have this? YES — and reinventing it would be the defect.** `eval/golden.py`
already carries `evaluate()` (`:98`), `regressions()` (`:118`) and `load_baseline()` (`:94`) over a
hand-blessed baseline. §2.5 says why it is the *right* instrument and not merely an available one:
**non-negotiable #9 makes the frozen golden set a fixed point — never auto-modified — so it is
stable across the migration by construction**, which is exactly what a cross-runtime baseline
needs. Use it. Do not write a second evaluator, a second corpus, or a second baseline.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — what does the measured ground actually say?** §2.1 F: 20 diverse texts (prose, notes,
  code, SQL, multilingual, degenerate single tokens) embedded under both runtimes on the
  **identical blob**: cross-runtime cosine **min 0.999990, mean 0.999999, max 1.000000**; the worst
  case is the single token `"the"`. Within-runtime repeat and single-vs-batch floors are
  **1.000000** everywhere. Dims 2560 both sides.
- **Q2 — why is the tolerance tight rather than "close enough"?** Because σ is load-bearing well
  beyond retrieval. `similarity_threshold = 0.62` **is σ**, the thought-graph edge threshold, and
  `config/defaults.toml:267-272` states its bound σ ∈ [0.55, 0.75] and calls the right value
  *"corpus- and embedder-specific."* `near_dup_threshold = 0.93` carries its own bound ≥ 0.90
  (`:276-277`), and `[dream_rnd] sigma = 0.62` (`:286`). A vector shift silently invalidates every
  σ-thresholded instrument — thought-graph edges, theme clustering, merge detection — not just
  retrieval.
- **Q3 — is the proposed gate defensible against those bounds?** **Yes, and the config makes it
  stronger than the note's own argument.** The note reasons from `near_dup = 0.93` with ~0.07 of
  cosine margin to identity. The config additionally pins a **hard lower bound of 0.90**
  (`:276-277`), i.e. only 0.03 of downward room before the threshold leaves its declared valid
  range. A 1e-3 shift is still 30× under *that* tighter margin, and the measured deviation (1e-5)
  is two orders below the gate. **Bit-identity is explicitly NOT the bar** (different backends,
  different batching); ≤1e-4 is acceptable *because* it is three orders below any decision boundary
  the system holds.
- **Q4 — can the harness write to `eval/golden/`?** ⚑ **No, never.** `eval/golden.py` and
  `eval/golden/**` are on the **foundation denylist** (CLAUDE.md) and are non-negotiable #9's fixed
  point. The harness **reads the fixtures and runs `evaluate()`**; it writes only its own report.
  A harness that regenerated the baseline to make itself pass would be the most complete possible
  failure of this plan.
- **Q5 — what is the generation-side bar?** §2.5: **not** string equality over sampled output —
  that is the wrong bar for a sampled process. Seed-pinned greedy determinism as a sanity check
  (measured reproducible, §2.1 G: temp 0, seed 42 reproduced identically across runs) plus the
  golden/drift gauges for behaviour.
- **Q6 — can the chat side be exercised at all?** ⚑ **Not against a real chat model, and the plan
  must say so.** §2.1 E: Ollama's chat blobs fail to load upstream (`qwen35` arch,
  `key qwen35.rope.dimension_sections has wrong array length; expected 4, got 3`). Only the
  **embedder blob is portable** — *which is the only reason equivalence was testable at all*. The
  generation half of this harness is therefore written and unit-tested but **cannot be run
  end-to-end until V-B** (owner-fetched upstream GGUFs, bp-119).
- **Q7 — ⚑ can the attestation record carry backend + build?** **NO — answered at graduation, as
  §2.5 asked.** The note says *"field availability to be confirmed at graduation"* and parks the
  decision as *"yes if the existing record shape carries it without schema change; else a V."*
  `Attestor.emit` (`core/attestation/attestor.py:36-45`) takes a **fixed keyword set** —
  `agent_role`, `action`, `input_hashes`, `output_hashes`, `derived_from_ids`,
  `vault_token_accessor` — and **no free-form metadata field**. The call site confirms it
  (`core/ingest/sync.py:120-124` passes four of them). ⇒ **The parked decision resolves to "a V",
  not "free".** Stamping provenance requires an attestation schema change, which is out of scope
  here and is recorded in §11 as an open item for bp-118.
- **Q8 — where does the harness spawn its server?** **Through bp-116's `ProcessManager`, not
  its own `subprocess` call.** `eval/` re-implementing spawn+health+kill would duplicate the
  manager and drift from it — the owner's DRY rule treats that as a defect, not a nit. This is the
  substantive reason this plan depends on bp-116 rather than only on bp-115.

**Additional risks or questions surfaced during reading:**

- ⚑ **"Worst case, not mean"** is stated twice in §2.5 and is the easiest thing to get wrong: a
  mean of 0.999999 with one text at 0.998 **fails**. Report and gate on the per-text minimum.
- The harness must be runnable standalone (§4: `uv run python -m eval.runtime_equivalence`) because
  it is **the artefact the deskcheck shows**. A harness that only runs under pytest cannot serve
  that role.
- Determinism must be established *within* each runtime before comparing *across* them. §2.1 F
  measured within-runtime floors of 1.000000; if that does not reproduce here, a cross-runtime
  number means nothing.

## 4. Reconciliation  <!-- Part B -->

- **`eval/golden.py`** → ⚑ **cross-ref: extension, and NOT edited.** The new module imports and
  calls it. Its docstring must **not** be amended to mention the new consumer — it is on the
  foundation denylist, and the whole reason it is the right baseline is that it does not change.
  The cross-reference lives in `eval/runtime_equivalence.py`'s own docstring, pointing *at* it.
- **`config/defaults.toml:267-272`** — *"calibrate on the owner's own corpus (the right σ is
  corpus- and embedder-specific) before trusting cluster boundaries"* → **cross-ref: extension**,
  in the harness docstring: this gate is what keeps that calibration valid across a runtime change.
  **Do not edit the config** — no threshold moves in this plan.
- **`dn-local-model-runtime` §2.5's parked stamping decision** → **cross-ref**, resolved by §3 Q7.
  Record the answer in the journal; a builder may not edit a ratified note.

## 5. Write scope

Exactly two files: `eval/runtime_equivalence.py` (the harness) and
`tests/unit/test_runtime_equivalence.py` (its own tests). This is the narrowest scope in the wave,
deliberately — the gate must be auditable at a glance.

⚑ Deliberately OUT of scope, and this is the load-bearing part of this section:
- **`eval/golden.py` and `eval/golden/**`** — **foundation denylist. READ and RUN, never write.**
  Non-negotiable #9: the frozen golden set is never auto-modified; human-only, deliberate, logged.
- **`config/defaults.toml`** — no σ, no threshold, no `[runtime]` key moves here.
- **`core/**`** — the harness observes; it changes nothing it measures.
- Every design note.

## 6. Interfaces pinned inline

**The tolerance — proposed from data in §2.5, ratified with the note:**

```
PASS          per-text cross-runtime cosine >= 0.9999 on EVERY fixture text
              AND regressions(report, load_baseline()) is empty
DISQUALIFYING any text < 0.999  =>  STOP the migration at the current lane

Measured worst case: 0.999990  (10x headroom under the pass bar)
Measured mean:       0.999999      max: 1.000000      within-runtime floor: 1.000000
Bit-identity is explicitly NOT the bar (different backends, different batching).
```

⚑ **Gate on the per-text MINIMUM, and report it.** §2.5 says "worst case reported, not mean" twice.

**The existing harness — its exact current signatures** (`eval/golden.py`; copied so the builder
never has to open a denylisted file to recall an API):

```python
def load_baseline(path: Path = BASELINE_PATH) -> dict[str, float]:            # :94
def evaluate(golden: Sequence[GoldenQuery], retriever: Retriever) -> GoldenReport:   # :98
def regressions(report: GoldenReport, baseline: dict[str, float]) -> list[str]:      # :118
```

`regressions` returns the metric names that fell below the blessed baseline: `recall_at_k` and
`overlap` are higher-is-better, `mean_distance` is lower-is-better within `distance_tol`
(default 0.05, `:129`). **Empty list = pass.**

**The three-part harness, verbatim from §2.5:**

```
1. embed eval/golden/corpus/ fixtures + golden_set.json queries under BOTH backends via the
   §2.6 client seam, and assert the per-text tolerance above (worst case reported, not mean);
2. run evaluate(golden, retriever) with the llama.cpp-backed retriever and assert
   regressions(report, load_baseline()) is empty — the frozen golden set is non-negotiable #9's
   fixed point, stable across the migration BY CONSTRUCTION;
3. re-run on every runtime version bump (the pinned-build discipline, §2.6) — the mechanical
   residue of the deleted per-bump uncertainty (§2.2).
```

**The generation bar — different, and deliberately looser** (§2.5):

```
NOT string equality over sampled output. Seed-pinned greedy decode (temp 0, seed 42 — measured
reproducible, §2.1 G) as a determinism sanity check, plus the golden/drift gauges for behaviour.
```

**The σ-thresholded instruments this protects** (`config/defaults.toml`):

```
similarity_threshold = 0.62   # :272  IS σ — thought-graph edges; BOUND σ ∈ [0.55, 0.75]
near_dup_threshold   = 0.93   # :277  merge detection;            BOUND ≥ 0.90
[dream_rnd] sigma    = 0.62   # :286  mirror-graph edges
```

**The standalone entrypoint** (§4 — it is the deskcheck artefact):

```
uv run python -m eval.runtime_equivalence
```

## 7. Items

Blast radius: within-runtime determinism → cross-runtime embeddings → retrieval → the report.

### Item 1 — determinism within each runtime

- **Objective:** establish the floor a cross-runtime number is measured against.
- **Files:** `eval/runtime_equivalence.py`, `tests/unit/test_runtime_equivalence.py`
- **Acceptance test:** repeat-embedding the same text under one backend gives cosine **1.000000**;
  single-vs-batch embedding of the same text agrees to the same floor. Both backends.
- **Falsifier:** ⚑ *the within-runtime floor is below 1.0.* Then the backend is nondeterministic
  and **no cross-runtime comparison means anything** — the whole gate is void until that is
  explained. §2.1 F measured 1.000000 everywhere, so a lower value here is a real discrepancy.
- **Invariant(s) it must not violate:** `eval/golden/**` is read-only; no fixture is regenerated.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — cross-runtime embedding equivalence, gated on the worst case

- **Objective:** the per-text tolerance is measured and enforced over the real fixture corpus.
- **Files:** `eval/runtime_equivalence.py`, `tests/unit/test_runtime_equivalence.py`
- **Acceptance test:** every text in `eval/golden/corpus/` plus every query in `golden_set.json` is
  embedded under both backends through the `InferenceClient` seam; the report carries the
  **per-text minimum**, the mean, and the identity of the worst text; the gate passes at ≥0.9999
  and **STOPs** below 0.999.
- **Falsifier:** ⚑ *the gate passes on the mean while a text sits below the bar.* This is the
  single most likely way to build this wrong, and it would let a real shift through. Test it
  directly: inject a synthetic vector one text of which is at 0.998 and assert the harness fails.
- **Invariant(s) it must not violate:** identical blob on both sides (§2.1 E — the embedder blob is
  the portable one); same dims (2560); **no fixture written**.
- **Touches stored data?** No — vectors are computed and compared in memory, never landed.
  ⚑ **The harness must never write to `data/vectors.lance`**; mixing provenances in the live store
  is the exact hazard it exists to prevent.
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — retrieval equivalence against the blessed baseline

- **Objective:** `regressions()` is empty with the llama.cpp-backed retriever.
- **Files:** `eval/runtime_equivalence.py`, `tests/unit/test_runtime_equivalence.py`
- **Acceptance test:** `evaluate(golden, retriever)` runs with a retriever backed by the new
  runtime over a **scratch** index built from the frozen fixtures, and
  `regressions(report, load_baseline())` returns `[]`.
- **Falsifier:** ⚑ *the harness regenerates or edits the baseline to make itself pass.* Foundation
  denylist, non-negotiable #9. Assert in the test that `eval/golden/` is byte-unchanged after a
  full run — a checksum before and after.
- **Invariant(s) it must not violate:** `eval/golden.py` is imported and called, never
  re-implemented; the scratch index is disposed; the live store is untouched.
- **Touches stored data?** No (scratch only). **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — the standalone report, and the generation sanity check

- **Objective:** the deskcheck artefact exists and is honest about what it did not test.
- **Files:** `eval/runtime_equivalence.py`, `tests/unit/test_runtime_equivalence.py`
- **Acceptance test:** `uv run python -m eval.runtime_equivalence` prints the worst-case cosine,
  the worst text, the mean, the golden report and the pass/fail verdict, and exits non-zero on
  failure. The generation half (seed-pinned greedy determinism) is implemented and unit-tested,
  and the report states explicitly that it was **NOT run against a real chat model** and why
  (§3 Q6, V-B).
- **Falsifier:** ⚑ *the report implies the chat tiers were validated.* §2.1 E makes that impossible
  today. An equivalence report that overstates its coverage is worse than none, because bp-119 would
  be blessed against it.
- **Invariant(s) it must not violate:** exit code is the gate; the report names the runtime build
  string it ran against (a result without a build identity cannot be re-checked on a bump, which is
  the whole point of part 3).
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 3.

## 8. Math carried explicitly

- **Cross-runtime cosine similarity** — *measures:* the angular agreement between two embeddings of
  the same text produced by two runtimes on the same weights. *valid when:* both sides use the
  identical GGUF blob and the same dimensionality (2560), and within-runtime determinism has been
  established first (Item 1) so the residual is attributable to the runtime and not to sampling.
  *fails its keep if:* the within-runtime floor is below 1.0 (the measurement has no baseline), or
  if it is reported as a **mean** — a mean hides exactly the tail case the gate exists to catch,
  and the measured worst case (the single token `"the"`) is precisely such a tail.

- **The tolerance bound, justified rather than chosen** — the tightest live decision boundary is
  `near_dup_threshold = 0.93` with a declared valid range ≥ 0.90 (`config/defaults.toml:276-277`),
  i.e. 0.03 of room. The disqualifying bar (1e-3) sits **30× under** that room; the pass bar (1e-4)
  sits 300× under; the measured deviation (1e-5) sits 3000× under. *fails its keep if:* any σ
  threshold is ever tightened to within an order of magnitude of the gate, at which point the gate
  must tighten with it.

## 9. Non-goals

- ⚑ **No writing to `eval/golden.py` or `eval/golden/**`** — foundation denylist, non-negotiable #9.
- **No cutover, no flip** — bp-118.
- **No production monitoring.** §2.5: this is a tier-4 ratchet, a point-in-time proof. It does not
  watch production and must not be described as if it does.
- **No σ recalibration, no threshold change, no chunking change** (`dn-local-model-runtime` §1.2).
- **No re-embed of the corpus** — the harness computes in memory and lands nothing.
- **No claim that chat was validated** (§3 Q6).
- **No second evaluator, corpus, or baseline** (§2, DRY).

## 10. Stop-and-raise conditions

- ⚑ **Any fixture text falls below 0.999 cross-runtime** ⇒ **STOP THE MIGRATION** at the current
  lane. This is the note's own disqualifier, not a threshold to negotiate. File and raise.
- ⚑ **`regressions()` is non-empty** ⇒ **STOP.** Same standing.
- ⚑ **Item 1's falsifier fires** — a runtime is nondeterministic ⇒ **STOP.** Every downstream
  number is meaningless until it is explained.
- ⚑ **Making the gate pass would require touching `eval/golden/`** ⇒ **STOP immediately and file.**
  That is a foundation-denylist write, and wanting to do it is itself the signal that the runtimes
  disagree.
- **The tolerance looks wrong against the measured data** ⇒ park and raise; the tolerance is an
  **owner call at ratification** and the note is ratified with these numbers — a builder does not
  move them.
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| stamping backend+build | ⚑ **needs a schema change — resolves to "a V"** | bp-118 decides |
| generation-side coverage | wire-contract + unit only | V-B: upstream chat GGUFs (bp-119) |
| where the report is written | stdout + exit code | a CI consumer needs a file |
| re-gate cadence | every runtime version bump | §2.6's pinned-build discipline |

**Rejected alternatives, per row:**

- ⚑ **Attestation stamping.** §2.5 asked graduation to confirm field availability; §3 Q7 answers it:
  `Attestor.emit` has a **fixed keyword set with no free-form field**
  (`core/attestation/attestor.py:36-45`), so the note's *"yes if it carries it without schema
  change"* branch is **false** and the *"else a V"* branch applies. Rejected: *stuff it into
  `action` or an existing hash field* — that would corrupt the attestation chain's semantics to
  carry unrelated metadata. Rejected: *widen the schema here* — out of scope, and attestation is
  provenance substrate that deserves its own deliberate change.
- **Generation coverage.** Forced by §2.1 E, not chosen.
- **Report destination.** Rejected: *a file under `data/`* — the harness must write nothing that
  could be mistaken for corpus state.
- **Re-gate cadence.** Rejected: *once at cutover* — §2.2 is explicit that the migration deletes
  the *recurrence* of the per-bump question only if the gate is mechanically re-run; a one-shot gate
  re-opens the uncertainty on the first `brew upgrade`.

## 12. Dependency & ordering summary

Items strictly linear: **1 → 2 → 3 → 4.** Determinism before comparison before retrieval before
report — each step is meaningless without the one before it.

**`depends_on: [bp-116]`** for two reasons, one substantive and one DRY: the harness needs a live
llama-server, and it **spawns it through the `ProcessManager`** rather than re-implementing
spawn/health/kill inside `eval/` (§3 Q8). Transitively after bp-115.

**Not parallelizable with anything** — though its write_scope is disjoint from every other plan's,
it cannot run before the manager exists.

⚑ **bp-118 and bp-119 both HARD-depend on this plan passing**, not merely on it existing. §2.5:
*"cutover is per-lane all-or-nothing, gated on measured equivalence."* A green harness is the
precondition; a red one stops the wave. This is the one plan in the runtime wave whose *result*,
not just its completion, gates what follows — and the owner's deskcheck of its report is what
authorizes the flip.

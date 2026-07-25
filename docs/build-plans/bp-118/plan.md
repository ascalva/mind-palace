---
type: build-plan
id: bp-118
track: ops
status: proposed
design_ref:
  - docs/design-notes/dn-local-model-runtime.md
contract: builder
write_scope:
  - core/ingest/embed.py
  - core/models/manager.py
  - eval/runtime_equivalence.py
  - ops/lifecycle/launcher.py
  - config/defaults.toml
  - tests/unit/test_embedder_cutover.py
  - tests/integration/test_runtime_wiring.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 220k
  actual: null
depends_on: [bp-117]
parallelizable_with: []
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0174.md
  - docs/findings/finding-0199.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0174.md
---

# Build Plan — P4: the embedder cuts over first (biggest win, smallest risk, provable)

## 0. Mode & provenance

**P4 of `dn-local-model-runtime` §2.6**, and the ordering is deliberate, verbatim: *"The embedder is
where the migration bites hardest and risks least: the blob is portable (§2.1 E), equivalence is
provable to 1e-5 (F), the accounting win is largest (10 → 3.7 GB, C), and it is the
corpus-critical path."*

⚑ **This plan does not perform the cutover. The owner does.** The deliverable is everything up to
and including a deskcheckable shadow-run report; the flip of
`[runtime] embedding_backend = "llamacpp"` in `config/local.toml` is an owner action (§4 of the
note, and standing policy: deploy-class changes are owner-in-loop). A builder that flips it has
crossed a gate.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.

## 1. Objective

The embedding role can run on palace-owned llama-server with proven-equivalent output, and the
evidence the owner needs to flip it — and to flip it back — exists.

### 1.2 Non-goals (explicit — see §9)

Not the chat tiers (bp-119, blocked on V-B). Not a model change, not a re-embed, not σ
recalibration (all `dn-local-model-runtime` §1.2). Not retiring `OllamaClient` — it is the standing
rollback until every role has flipped.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-local-model-runtime.md` — **§2.5** (the gate this consumes), **§2.6 P4**,
   §2.3 (the embed-ctx right-sizing), §4 (the wiring and the flip), **V-D, V-E** — the content spec
2. `docs/build-plans/bp-117/plan.md` — the harness and its report format; **read its §6 tolerance
   pin, do not re-derive it**
3. `docs/build-plans/bp-116/plan.md` §6 — the manager and the budget gate
4. `docs/build-plans/bp-115/plan.md` §6 — the `[runtime]` schema and the client protocol
5. `core/ingest/embed.py` — the facade the whole corpus pipeline uses
6. `docs/findings/finding-0174.md` — the warrant, now 4× worse than filed

**Does core already have this?** bp-117's harness is the equivalence machinery — **extend it with a
shadow mode, do not write a second comparator.** bp-116's manager is the spawn machinery. This plan
writes almost no new mechanism; it wires, measures, and reports.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — ⚑ which config key is authoritative?** The note names it **two ways**: §2.6 P4 says
  *"the owner flips `[embedding] backend = "llamacpp"`"*, while §4 (the Wiring & enablement
  section) says *"the owner flips `[runtime] embedding_backend = "llamacpp"`"*. **§4 governs
  wiring**, and bp-115 landed `[runtime] embedding_backend` accordingly (its §6). This plan uses
  `[runtime]`, and §4 of this plan records the discrepancy rather than silently choosing.
- **Q2 — what is the accounting win, concretely?** §2.1 C: the embedder under Ollama runs at
  **10.0 GB** at its model-default ctx 40960, because `OllamaClient.embed()` passes no `num_ctx`
  (`core/models/ollama_client.py:97-104`). Under palace-launched llama-server at ctx 8192 the same
  blob is **RSS 3.69 GB**. ≈6.3 GB recovered, and finding-0174's invisible consumer enters the
  books by construction (bp-116).
- **Q3 — V-D: can any palace embed call exceed ctx 8192?** Two call paths, both through
  `core/ingest/embed.py`: `embed_documents` (`:29-32`) over chunks capped at `max_chars = 1200`
  (`config/defaults.toml:109`), far under 8k tokens; and `embed_query` (`:31-34`), which wraps a
  single query in `"Instruct: …\nQuery: …"`. **The chunk path is safe by the cap. The query path is
  not bounded by anything** — a very long owner query would flow straight through. Item 1 must
  measure the actual bound and confirm the typed `exceed_context_size_error` (§2.1 G) surfaces
  loudly if one does. **The code does not settle the query path's worst case.**
- **Q4 — V-E: what batch size keeps cancellation bounded?** §2.1 G measured it: a **256-input
  batch** gives ~20 s cancel granularity (slot freed in ~20 s vs ~95+ s had it kept computing).
  §2.9's falsifier: *wrong if client-side embed batches make cancel granularity exceed the batch
  budget*. So the embed batch size must be pinned against `dn-supervision-and-liveness` §2.5's
  batch clock — this is the one place the two notes' mechanisms meet numerically.
- **Q5 — why is no re-embed needed in either direction?** §2.5: *"if the runtimes agree beyond
  σ-resolution, provenance mixing is harmless."* The gate at 1e-4 sits three orders under any
  decision boundary the system holds (bp-117 §8). **This is the ONLY thing that makes rollback
  free**, and it is why the gate is a precondition rather than a report.
- **Q6 — what does the shadow run compare?** §2.6 P4: *"both backends embedding the fixture set +
  a sample of live traffic compared offline."* The fixture half is bp-117's harness. The
  **live-traffic half is new** and is the part that catches what a curated fixture corpus cannot:
  real notes, real code, real chat transcripts, with whatever degenerate inputs the corpus actually
  contains.
- **Q7 — what does `status` show after the flip?** §4: process residency (pid, RSS vs budget,
  `/slots` busyness) *"in place of today's belief-derived line"*. Today's line is
  `_embedder_state` (`ops/lifecycle/launcher.py:1080-1098`), which asks Ollama's `ps()`. Under
  llamacpp that answer comes from the process table instead. **Both must work** — the render is
  conditional on the configured backend, because Ollama remains the rollback.

**Additional risks or questions surfaced during reading:**

- ⚑ **The rollback must be tested, not assumed.** A cutover whose rollback has never been exercised
  is a one-way door wearing a two-way sign. Item 4 exercises the flip back.
- ⚑ **A silent fallback would be catastrophic here.** If `embedding_backend = "llamacpp"` is set
  but the server fails to start and the code quietly falls back to Ollama, the owner believes the
  cutover happened while it did not — and the shadow evidence would be about a configuration that
  is not running. bp-116 Item 5 already makes misconfiguration fail loudly; this plan must not
  weaken it.
- The live-traffic sample must be read-only. Embedding a sample of the corpus is safe; **landing
  any of those vectors is not** — that is the two-provenance hazard §2.5 exists to prevent.

## 4. Reconciliation  <!-- Part B -->

- ⚑ **`dn-local-model-runtime` §2.6 P4 vs §4** — the config key discrepancy (§3 Q1). → **Recorded,
  not edited**: the note is ratified and therefore agent-immutable. The journal must record that
  §4's `[runtime] embedding_backend` was taken as authoritative because §4 is the wiring section
  and bp-115 built to it. If the owner intended `[embedding] backend`, that is a §10 raise.
- **`ops/lifecycle/launcher.py:1080-1098`** — `_embedder_state`'s docstring, which describes the
  signal as *"is the embedding model loaded in the local Ollama?"* → **banner: correction.** After
  this plan the question can be answered two ways depending on the backend. Keep its honest
  framing (*"this line is corroboration, not the alarm"*) — that qualification is bp-102's and
  remains true.
- **`config/defaults.toml:105-119`** — the `[embedding]` section → **cross-ref: extension.** It
  gains no backend key (that lives in `[runtime]`, §3 Q1); cross-reference so a reader looking for
  the backend finds it. **Do not move `model` or `dim`** — a model change is an owner-stated
  non-goal.
- **`docs/findings/finding-0174.md`** → **cross-ref: extension.** It closes only when the flip
  happens, which is the owner's act. Record the evidence; the orchestrator closes it at seal, and
  only if the flip has actually occurred (completion-claims honesty).

## 5. Write scope

`core/ingest/embed.py` carries the batch-size pin (V-E) and the backend selection through bp-115's
factory. `core/models/manager.py` carries the embedder role's ctx and budget wiring.
`eval/runtime_equivalence.py` is **extended** with the live-traffic shadow mode (sequential
ownership after bp-117 — same file, different session, never concurrent).
`ops/lifecycle/launcher.py` carries the conditional residency render. Two test files.

⚑ Deliberately OUT of scope: **`config/local.toml`** — the flip itself is the owner's and is not a
tracked file; **`eval/golden.py` and `eval/golden/**`** — foundation denylist; `data/vectors.lance`
— nothing this plan runs may write a vector to it (§3, additional risks); every design note.

## 6. Interfaces pinned inline

**The gate that must be green before anything here ships** (bp-117 §6, copied so it is visible at
the point of use):

```
PASS          per-text cross-runtime cosine >= 0.9999 on EVERY fixture text
              AND regressions(report, load_baseline()) is empty
DISQUALIFYING any text < 0.999  =>  STOP the migration at the current lane
Gate on the per-text MINIMUM. Measured worst case 0.999990; mean 0.999999.
```

**The cutover position, verbatim from §2.5:**

```
Cutover is PER-LANE ALL-OR-NOTHING, gated on measured equivalence — not a blind atomic swap, and
not a forced re-embed. If the gate ever fails after a cutover, the recovery is a full re-embed
from raw (§8 re-derivability) — never a knowingly mixed store.
```

**The flip — the owner's action, recorded here so the deskcheck can state it exactly:**

```toml
# config/local.toml — OWNER ACTION, not a builder's
[runtime]
embedding_backend = "llamacpp"
```

Rollback is the same edit reversed. **Gate-proven vector agreement means no re-embed in either
direction** (§2.6 P4).

**V-E's measured cancellation bound** (§2.1 G) — the number the batch size must respect:

```
256-input embed batch  =>  ~20 s cancel granularity (slot freed ~20 s; vs ~95+ s uncancelled)
Constraint: cancel granularity <= dn-supervision-and-liveness §2.5's batch budget.
```

**The embedder role's parameters** (§2.3):

```
model  qwen3-embedding:4b      ctx 8192 (from the model default 40960)      budget 3.69 GB RSS
```

**`Embedder`'s public surface — unchanged, and 30+ test files depend on it**
(`core/ingest/embed.py:22-34`): `dim`, `embed_documents`, `embed_query`.

## 7. Items

Blast radius: read-only measurement → in-memory shadow comparison → config-selected routing →
the reversibility proof → the render.

### Item 1 — V-D and V-E: bound the inputs and the cancellation

- **Objective:** the ctx and batch-size choices are measured, including the unbounded query path.
- **Files:** `core/ingest/embed.py`, `tests/unit/test_embedder_cutover.py`
- **Acceptance test:** journal records the token-length distribution of real chunks (bounded by
  `max_chars = 1200`) **and the worst case of the query path** (§3 Q3, which the code does not
  bound); a query that would exceed ctx 8192 produces the typed `exceed_context_size_error`
  **loudly**, never a truncated silent embedding. Embed batch size is pinned so cancel granularity
  ≤ the supervision batch budget.
- **Falsifier:** ⚑ *an over-length input is silently truncated rather than raising.* A truncated
  embedding is a *wrong vector that looks fine* — it lands in the corpus and no instrument detects
  it. This is the same class as the two-provenance hazard, one input at a time.
- **Invariant(s) it must not violate:** `Embedder`'s public surface is unchanged; no vector is
  landed.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — the live-traffic shadow run

- **Objective:** equivalence is demonstrated on the real corpus, not only on curated fixtures.
- **Files:** `eval/runtime_equivalence.py`, `tests/unit/test_embedder_cutover.py`
- **Acceptance test:** a sampled slice of live corpus text (notes, code, chat) is embedded under
  **both** backends and compared **offline, in memory**; the report carries the per-text minimum,
  the worst text verbatim, the mean, and the sample's composition. The gate's bars apply unchanged.
- **Falsifier:** ⚑ *a live-corpus text falls below the fixture worst case.* The fixture corpus is
  curated; the live one contains whatever it contains, and §2.1 F's worst case was a degenerate
  single token — exactly the kind of input a curated set under-represents. A live sample that is
  *worse* than fixtures is the expected direction and must be gated, not explained away.
- **Invariant(s) it must not violate:** ⚑ **nothing is written to `data/vectors.lance`** — the
  shadow run computes and compares in memory; landing a shadow vector would create the exact mixed
  store the gate exists to prevent. Read-only against the corpus.
- **Touches stored data?** ⚑ **Reads the live corpus; writes nothing.** Assert the store's row
  count and version are unchanged after a run.
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — the embedding role routes by config

- **Objective:** `build_embedder` honours `[runtime] embedding_backend`, defaulting to `ollama`.
- **Files:** `core/ingest/embed.py`, `core/models/manager.py`,
  `tests/integration/test_runtime_wiring.py`
- **Acceptance test:** with defaults, behaviour is byte-identical to today; with
  `embedding_backend = "llamacpp"`, `build_embedder` returns a manager-backed embedder, the server
  is spawned budget-gated and health-gated, and a misconfigured `server_binary` **fails loudly at
  startup**.
- **Falsifier:** ⚑ *a failed llamacpp start silently falls back to Ollama.* The owner would believe
  a cutover happened that did not, and every subsequent observation would be about the wrong
  configuration (§3, additional risks). Test it: break the binary path and assert a loud failure,
  not a working system.
- **Invariant(s) it must not violate:** the budget gate refuses before spawning (bp-116); the
  embedder is inside the books; `[embedding] model` and `dim` are untouched.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — the rollback is exercised, not assumed

- **Objective:** flipping back is proven to be a no-op for the corpus.
- **Files:** `tests/integration/test_runtime_wiring.py`, `tests/unit/test_embedder_cutover.py`
- **Acceptance test:** embed a scratch corpus under `llamacpp`, flip the config back to `ollama`,
  and demonstrate that **retrieval over the mixed scratch store still passes the golden gate** —
  which is exactly the claim §2.5 makes ("provenance mixing is harmless" **because** the gate
  holds) and the one that must not be taken on faith.
- **Falsifier:** ⚑ *the mixed scratch store fails the golden gate.* Then §2.5's central claim is
  false, no-re-embed rollback is not available, and the cutover is a one-way door — **STOP the
  wave** and return the note to the owner.
- **Invariant(s) it must not violate:** scratch store only; the live corpus is never mixed as an
  experiment.
- **Touches stored data?** No (scratch). **Parallelizable?** No. **Depends on:** Item 3.

### Item 5 — `status` tells the truth about residency

- **Objective:** the residency line reports process facts under llamacpp and Ollama facts under
  Ollama.
- **Files:** `ops/lifecycle/launcher.py`, `tests/integration/test_runtime_wiring.py`
- **Acceptance test:** under `llamacpp`, `status` renders pid, RSS vs budget and `/slots` busyness;
  under `ollama` it renders today's `_embedder_state` line unchanged. `status` stays cheap
  (`tests/unit/test_status_cost_bound.py` still passes).
- **Falsifier:** ⚑ *`status` gets more expensive*, or *the render cannot distinguish "no server"
  from "server unreachable"*. The second matters: those are opposite operator actions, and
  collapsing
  them re-creates the ambiguity bp-102 spent a plan removing.
- **Invariant(s) it must not violate:** bp-105's `embedding: YES / ⚠ WEDGED` line
  (`launcher.py:1161-1169`) and the ORPHANED render are kept; the status seam stays `build_status`.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 3.

## 8. Math carried explicitly

- **The per-text cross-runtime cosine minimum over a live sample** — *measures:* the worst
  disagreement between runtimes on text the corpus actually contains. *valid when:* the sample is
  drawn across provenances (notes, code, chat) rather than one lane, and includes short/degenerate
  inputs — §2.1 F's worst case was the single token `"the"`, so a sample of only long prose would
  systematically overstate agreement. *fails its keep if:* it is reported as a mean, or if the
  sample is drawn from one provenance.

## 9. Non-goals

- ⚑ **No flip.** The owner performs it (§0, §4 of the note). A builder that edits
  `config/local.toml` has crossed a gate.
- **No re-embed of the corpus**, in either direction — the gate is what makes that unnecessary.
- **No chat tiers** — bp-119, blocked on V-B.
- **No model change, no σ recalibration, no chunking change** (§1.2 of the note).
- **No retiring `OllamaClient`** — the standing rollback.
- **No writing to `eval/golden/**`** — foundation denylist.
- **No landing of any shadow vector** (§7 Item 2).

## 10. Stop-and-raise conditions

- ⚑ **bp-117's gate is not green** ⇒ **do not start.** §2.5: cutover is gated on measured
  equivalence. This is a precondition, not a checklist item.
- ⚑ **Item 4's falsifier fires** — a mixed scratch store fails the golden gate ⇒ **STOP THE WAVE.**
  §2.5's no-re-embed-in-either-direction claim would be false and the cutover would be a one-way
  door. Return the note to the owner.
- ⚑ **A live-sample text falls below 0.999** ⇒ **STOP.** Same standing as the fixture bar.
- ⚑ **Item 1's falsifier fires** — an over-length input is silently truncated ⇒ **STOP.** A wrong
  vector that looks fine is undetectable downstream.
- **The config key discrepancy (§3 Q1) turns out to matter** — the owner intended
  `[embedding] backend` ⇒ raise; do not silently build both.
- **The flip appears necessary to complete an acceptance test** ⇒ STOP. Use a scratch config, never
  `config/local.toml`.
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| live-sample size | stratified by provenance; size in Item 2 | a lane under-represented |
| embed batch size | pinned to V-E's ≤20 s granularity | the supervision batch budget changes |
| stamping backend+build | ⚑ open — needs a schema change (bp-117 §3 Q7) | an owner call |
| Ollama retirement | not now — standing rollback | all roles flipped + deskcheck (bp-119) |

**Rejected alternatives, per row:**

- **Live sample.** Rejected: *fixtures only* — a curated corpus under-represents the degenerate
  inputs that produced the measured worst case. Rejected: *the whole corpus* — 22,621 rows embedded
  twice is a multi-hour run for a gate that a stratified sample settles.
- **Batch size.** Rejected: *maximize throughput* — it directly worsens cancel granularity, which
  is §2.9's named falsifier and couples to the supervision batch budget.
- ⚑ **Attestation stamping.** Graduation answered the note's "confirm at graduation" question:
  `Attestor.emit` has a fixed keyword set with no free-form field
  (`core/attestation/attestor.py:36-45`), so provenance stamping needs an attestation **schema
  change**. Rejected here: *widen the schema as part of the cutover* — attestation is provenance
  substrate and deserves a deliberate change, not a rider on a runtime flip. **Consequence to state
  plainly at the deskcheck: after this cutover, vector provenance is NOT recorded per-embed.** The
  gate is what makes that tolerable; it is not a reason to skip the gate.
- **Ollama retirement.** Rejected: *retire at P4* — every chat tier still runs on it.

## 12. Dependency & ordering summary

Items: **1 → 2 → 3 → {4, 5}.**

**`depends_on: [bp-117]`, and uniquely in this wave the dependency is on a RESULT, not a
completion**: bp-117's gate must be **green**. Transitively after bp-115 and bp-116.

**Not parallelizable with anything.** It extends `eval/runtime_equivalence.py` (bp-117's file,
sequentially) and touches `ops/lifecycle/launcher.py` (the wave's contended file: bp-108 → bp-111 →
bp-112 → bp-116 → **bp-118**).

⚑ **What "done" means here, precisely** (completion-claims honesty): this plan is complete when the
shadow report exists and is deskcheckable. **finding-0174 does not close and the cutover has not
happened until the owner flips the key.** A seal that reports "the embedder migrated" before that
flip is a false completion claim — the exact species the M2/K1 lesson (finding-0148) records.

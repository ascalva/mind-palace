---
type: build-plan
id: bp-119
track: ops
status: proposed
design_ref:
  - docs/design-notes/dn-local-model-runtime.md
contract: builder
write_scope:
  - core/models/manager.py
  - core/models/server.py
  - eval/runtime_equivalence.py
  - ops/lifecycle/launcher.py
  - ops/lifecycle/preflight.py
  - config/defaults.toml
  - tests/unit/test_chat_cutover.py
  - tests/integration/test_runtime_wiring.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 280k
  actual: null
depends_on: [bp-118]
parallelizable_with: []
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0174.md
  - docs/brainstorms/local-model-runtime.md
re_entry: "V-B cleared (upstream chat GGUFs load, quant verified) AND V-A measured; see §12"
supersedes: null
superseded_by: null
warrant: docs/brainstorms/local-model-runtime.md
---

# Build Plan — P5: the chat tiers, per-tier, each reversible (PARKED on V-B)

## 0. Mode & provenance

**P5 of `dn-local-model-runtime` §2.6**: *"chat tiers, per-tier (router → routine → synthesis →
stretch), each gated on golden + drift, each reversible by flag."*

⚑ **THIS PLAN IS PARKED AND MUST NOT BE BLESSED YET.** Its central prerequisite is **V-B**, and V-B
is not engineering work — it is an **owner/ops action outside the repository**: sourcing
upstream-convention GGUFs for the chat lineup. §2.1 E measured why: Ollama's chat blobs **do not
load** under upstream llama.cpp —

> `key qwen35.rope.dimension_sections has wrong array length; expected 4, got 3`

— for the whole `qwen35`-arch lineup (`qwen3.5:2b`, `qwen3.5:9b`, `qwen3.6:27b`). Ollama's bundled
fork accepts metadata upstream rejects; its model store has drifted from upstream conventions for
this family. **The embedder blob is the portable one, and that is the only reason equivalence was
testable at all.**

It is minted now rather than left implicit because a parked decision is a first-class artifact, not
a gap in a sequence — and because the wave's completion claim depends on knowing this is owed. The
`re_entry` field in the front-matter is the greppable gate.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval,
**after** the re-entry condition holds.

## 1. Objective

Each chat tier can run on palace-owned llama-server, flipped and rolled back independently, with
per-tier evidence from the golden and drift gauges.

### 1.2 Non-goals (explicit — see §9)

Not a model change — the GGUFs must be **the same models at matched quant** (owner-stated non-goal,
§1.2 of the note). Not MLX, not vLLM. Not the embedder (bp-118). [INFERENCE] Not a prompt or
persona change: §2.4 keeps personas injected at request time exactly as today, and a chat-format
difference between runtimes must be resolved by configuration, never by editing a persona —
inferred from the model-change non-goal.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-local-model-runtime.md` — **§2.1 E and G** (why the blobs fail; the
   measured server behaviour), **§2.6 P5 and Version pinning**, §2.3 (the three-process
   arithmetic), §2.5's generation bar, **V-A, V-B, V-H** — the content spec
2. `docs/build-plans/bp-118/plan.md` — the embedder cutover; its shadow-run and rollback pattern is
   the template this plan repeats per tier
3. `docs/build-plans/bp-117/plan.md` §6 — the gate, and §3 Q6: **the generation half was written
   but never run against a real chat model.** This plan is where it first runs.
4. `docs/build-plans/bp-116/plan.md` §6 — the manager, the argv capability, the stop ladder
5. `core/models/server.py` — `ModelServer.chat` `:32-43`; the tier→model routing
6. `config/defaults.toml` `[[models]]` — the tier lineup, `resident_gb`, `num_ctx`, `evicts_pinned`
7. `eval/golden.py` — **read and run, never write** (foundation denylist)

**Does core already have this?** bp-118 established the whole cutover pattern — shadow run, gate,
owner flip, exercised rollback, conditional status render. **Repeat it per tier; do not invent a
second cutover procedure.** bp-117's harness already contains the generation-side determinism check
(seed-pinned greedy); this plan runs it for the first time rather than writing it.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — ⚑ what exactly blocks this?** V-B. §2.1 E: the chat lineup fails to load upstream with a
  metadata-shape error (`rope.dimension_sections` expected 4, got 3). Sourcing replacements is
  **outside the core by design** (§2.4: model acquisition is an owner/ops action, exactly as
  `ollama pull` is today, and the spawn argv carries **no** download flag). No amount of building
  clears this.
- **Q2 — what must the replacement GGUFs satisfy?** §2.6 P5: *"quant matched to Ollama's (Q4_K_M
  lineage), placed locally."* Matched quant is what keeps this a runtime migration rather than a
  model change — the owner-stated non-goal. A different quant is a different model's behaviour and
  would invalidate every golden comparison.
- **Q3 — is the arithmetic known?** ⚑ **No — V-A.** §2.3's table carries `27b/35b = V-A`, and §2.9's
  falsifier is explicit: *wrong if V-A shows synthesis/stretch cannot fit even with the embedder
  stopped — then the ctx budgets or the tier lineup must change and the note returns to the owner.*
  bp-116 Item 1 measures it. This plan cannot size the stretch tier's policy before that.
- **Q4 — what is the generation-side bar?** §2.5: **never string equality over sampled output.**
  Seed-pinned greedy decode (temp 0, seed 42 — measured reproducible across runs, §2.1 G) as a
  determinism sanity check, plus the **golden and drift gauges** for behaviour. This is the correct
  bar because generation is sampled; an exact-match test would fail on a correct migration and pass
  on a broken one that happened to be deterministic.
- **Q5 — does the chat wire format differ?** llama-server speaks `/v1/chat/completions`
  (OpenAI-compatible, measured working, §2.1 G) while Ollama speaks `/api/chat`
  (`core/models/ollama_client.py:125`). bp-115's `LlamaServerClient` already implements the former
  against the wire contract. ⚑ **But chat templating is a live risk**: Ollama launches its bundled
  server with `--no-jinja --chat-template chatml` (§2.1 D, observed in the process argv). The
  palace's own spawn must produce the **same prompt bytes** for the same messages, or the model
  sees a different input and every comparison is confounded. **The code does not settle what
  template the replacement GGUFs carry** — Item 1 must establish it.
- **Q6 — is the SIGTERM wedge still present?** **V-H, and it must be re-measured here.** §2.1 G
  measured mid-request SIGTERM not exiting in 30.9 s (>3.5 min in a second observation), idle
  SIGTERM 0.25 s. §2.6's pinning discipline says a bump re-runs the gate **and** re-checks the
  wedge. A chat tier is where long generations live, so the wedge matters most here.
- **Q7 — what order do the tiers flip?** §2.6: router → routine → synthesis → stretch. Grounded:
  the router is pinned and smallest (2.5 GB, §2.3) so it is the cheapest to prove and the fastest
  to roll back; stretch is last because it is the one that `evicts_pinned` and therefore the one
  whose failure is most disruptive.
- **Q8 — when does Ollama retire?** §2.6: *"Ollama retires only after all tiers flip and a
  deskcheck passes; until then it remains the standing fallback."* **Retirement is not this plan's
  act** — it is a separate owner decision after the deskcheck.

**Additional risks or questions surfaced during reading:**

- ⚑ **The drift gauge is the behavioural instrument here**, and it must be run *before* the flip to
  establish a same-runtime baseline. Comparing post-flip drift against a baseline taken under
  Ollama months earlier would attribute normal corpus drift to the runtime.
- `ops/lifecycle/preflight.py:51-53` probes Ollama's `version()` to decide the system is ready. Once
  a tier runs on llamacpp, preflight must probe the right backend or it will pass while the actual
  serving path is down.
- Per §2.6's version pinning: the runtime is a **pinned brew version (or vendored binary — parked)**
  and a bump is a deliberate ops action that re-runs §2.5 + re-checks V-H. *"Never auto-updated —
  the exact property Ollama.app lacks."*

## 4. Reconciliation  <!-- Part B -->

- **`config/defaults.toml` `[[models]]`** — each tier's `resident_gb` is a weights-only declared
  constant → **banner: correction**, per tier, as each flips. bp-116 established that budgets are
  measured, not declared; this is where the chat tiers' numbers become measured. ⚑ **Do not change
  `name`, `tier`, or the quant lineage** — that would be a model change.
- **`ops/lifecycle/preflight.py:45-55`** — the Ollama version probe → **banner: correction.**
  It must probe the backend actually configured for each role, or it reports ready while the
  serving path is down (§3, additional risks).
- **`core/models/server.py:32-43`** — `ModelServer.chat` passes `keep_alive` from
  `self.config.ollama.default_keep_alive` (`:42`) → **banner: correction.** `keep_alive` is an
  Ollama residency concept with **no llama.cpp counterpart** (residency is process existence,
  §2.3). Under llamacpp it must be dropped, not translated — passing it would be meaningless at
  best and confusing at worst.
- **`docs/tracks/ops.md:16`** — OPS-7's DoD row → **cross-ref only.** The orchestrator judges it at
  seal; a builder does not close a track row.

## 5. Write scope

`core/models/manager.py` and `core/models/server.py` carry per-tier routing and the chat role's
process parameters. `eval/runtime_equivalence.py` is **extended** with the per-tier generation
comparison (sequential ownership after bp-117/bp-118). `ops/lifecycle/launcher.py` and
`ops/lifecycle/preflight.py` carry the render and the probe. `config/defaults.toml` carries the
measured per-tier budgets. Two test files.

⚑ Deliberately OUT of scope: **`config/local.toml`** — every flip is the owner's; **`eval/golden.py`
and `eval/golden/**`** — foundation denylist, read and run only; **the GGUF files themselves** —
owner-placed, never fetched by the core (§2.4, tier 2: the server is never *given* anything to dial
out for); `core/ingest/embed.py` (bp-118's, and already flipped); every design note.

## 6. Interfaces pinned inline

**⚑ The blocking measurement, verbatim** (`dn-local-model-runtime` §2.1 E):

```
Upstream llama-server loads Ollama's qwen3-embedding:4b blob directly (1.66 s to healthy, dims
2560 correct). The chat lineup (qwen3.5:2b/9b, qwen3.6:27b — all GGUF arch `qwen35`) FAILS to
load: "key qwen35.rope.dimension_sections has wrong array length; expected 4, got 3".
The load failure itself was fail-closed: process exit with a clear log, no zombie.
```

**The V-B acceptance, which is the re-entry condition:**

```
V-B — source upstream-convention GGUFs for the chat lineup; verify quant parity with the Ollama
tags (Q4_K_M lineage) and that b10090+ loads them. Blocks P5.
```

**The generation bar** (§2.5) — *different from the embedder's, and deliberately looser:*

```
NOT string equality over sampled output — that is the WRONG bar for a sampled process.
  * seed-pinned greedy decode (temp 0, seed 42) as a DETERMINISM sanity check
    (measured reproducible across runs, §2.1 G)
  * the golden set + the drift gauge for BEHAVIOUR
```

**The tier order** (§2.6): `router → routine → synthesis → stretch`. Each gated on golden + drift,
each reversible by flag, per-tier.

**Chat templating — the confound to eliminate** (§2.1 D, observed in Ollama's own process argv):

```
Ollama launches its bundled server with:  -c 8192 --no-jinja --chat-template chatml
The palace's spawn must produce the SAME prompt bytes for the same messages, or the model sees a
different input and every behavioural comparison is confounded.
```

**The stop ladder and the wedge** (§2.1 G, V-H — re-measure on the pinned build):

```
idle SIGTERM        0.25 s clean exit
mid-request SIGTERM WEDGED — no exit in 30.9 s (>3.5 min in a second observation); SIGKILL required
```

**Version pinning** (§2.6): a pinned brew version (or vendored binary — parked) with the build
string **asserted at spawn**; a bump is a deliberate ops action that re-runs §2.5 and re-checks
V-H. *"Never auto-updated — the exact property Ollama.app lacks."*

## 7. Items

Blast radius: verify the prerequisite → prove one small tier → generalize → the render → the
retirement recommendation (not the retirement).

### Item 1 — V-B and the template, verified before anything is built

- **Objective:** the replacement GGUFs load, match quant, and produce the same prompt bytes.
- **Files:** none (scratchpad; results in `journal.md`)
- **Acceptance test:** each owner-placed GGUF loads on the **pinned** build; its quant lineage is
  recorded and matches the Ollama tag; and for a fixed message list, the prompt bytes the palace's
  spawn produces are **byte-identical** to what Ollama's `--no-jinja --chat-template chatml`
  produces. V-H is re-measured on the pinned build.
- **Falsifier:** ⚑ *the prompt bytes differ.* Then every downstream behavioural comparison is
  confounded and a golden regression would be misattributed to the runtime. ⚑ Also: *the quant
  differs from the Ollama tag* — that is a **model change**, an owner-stated non-goal, and it
  invalidates the entire equivalence story.
- **Invariant(s) it must not violate:** the core never fetches a model (§2.4); measurement only.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — the router tier, end to end

- **Objective:** the smallest, cheapest tier proves the whole per-tier procedure.
- **Files:** `core/models/manager.py`, `core/models/server.py`, `eval/runtime_equivalence.py`,
  `tests/unit/test_chat_cutover.py`
- **Acceptance test:** the router runs on llama-server; seed-pinned greedy decode reproduces
  identically across runs and across backends; **a same-runtime drift baseline is taken BEFORE the
  flip** and the post-flip drift is compared against it (§3, additional risks); the golden gate is
  green; the config flip and flip-back are exercised on a scratch config.
- **Falsifier:** ⚑ *post-flip drift is compared against a stale Ollama-era baseline.* Normal corpus
  drift would then be attributed to the runtime — a false alarm that would stop a correct migration,
  or worse, be explained away and mask a real one.
- **Invariant(s) it must not violate:** `keep_alive` is dropped under llamacpp, not translated
  (§4); personas stay injected at request time; the router is pinned and its eviction semantics are
  unchanged.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — routine, synthesis, stretch — in that order

- **Objective:** each remaining tier flips independently, with its own evidence.
- **Files:** `core/models/manager.py`, `config/defaults.toml`, `eval/runtime_equivalence.py`,
  carried tests
- **Acceptance test:** per tier: measured RSS at the role ctx recorded into its budget, budget gate
  respected, golden + drift green, flip and flip-back exercised. The three-process arithmetic
  (§2.3) is re-checked for each: **synthesis @32k and stretch are the ones expected not to fit
  beside both housemates**, and the manager's stop-the-embedder (and for stretch, stop-the-router)
  policy is exercised rather than assumed.
- **Falsifier:** ⚑ *a tier's measured RSS breaches the budget sum with the documented eviction
  policy applied.* That is §2.9's three-process falsifier and it returns the note to the owner
  (§10) — it is not a number to adjust.
- **Invariant(s) it must not violate:** `evicts_pinned` semantics are preserved, now *verified*
  rather than hoped (§2.3); the budget refusal happens before spawn; no tier's model name or quant
  changes.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — preflight and status tell the truth per role

- **Objective:** readiness and residency are reported for the backend actually serving each role.
- **Files:** `ops/lifecycle/preflight.py`, `ops/lifecycle/launcher.py`,
  `tests/integration/test_runtime_wiring.py`
- **Acceptance test:** with a mixed configuration (some roles on Ollama, some on llamacpp) —
  **which is the expected steady state during this plan** — preflight probes each role's actual
  backend and `status` renders each role's true residency.
- **Falsifier:** ⚑ *preflight passes while a configured role's server is down.* `start` would then
  proceed into a system that cannot serve, and the operator's first signal would be a failed job.
- **Invariant(s) it must not violate:** `status` stays cheap; bp-105's diagnostic lines are kept.
- **Touches stored data?** No. **Parallelizable?** Yes, with Item 3. **Depends on:** Item 2.

### Item 5 — the retirement recommendation, not the retirement

- **Objective:** the owner has what they need to decide whether Ollama goes.
- **Files:** `tests/integration/test_runtime_wiring.py` (the "no Ollama" configuration test)
- **Acceptance test:** a test proves the system operates with **every role on llamacpp** and no
  Ollama process at all; the journal carries a per-tier evidence table (gate results, drift, RSS vs
  budget, wedge behaviour) as the deskcheck artefact.
- **Falsifier:** ⚑ *the journal reports Ollama "retired".* §2.6: it retires **after** all tiers flip
  **and a deskcheck passes**, and both the flips and the retirement are the owner's acts. Reporting
  otherwise is the completion-claim species finding-0148 records.
- **Invariant(s) it must not violate:** `OllamaClient` and the `[ollama]` config section are
  **not deleted** in this plan — they are the standing rollback until the owner says otherwise.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Items 3, 4.

## 8. Math carried explicitly

- **Seed-pinned greedy determinism** — *measures:* whether a sampled decoder, pinned to temp 0 and a
  fixed seed, produces identical token sequences across runs and across runtimes. *valid when:* the
  prompt bytes are identical (Item 1) and the quant is matched — otherwise it measures a different
  model, not a different runtime. *fails its keep if:* it is used as the *behavioural* bar rather
  than a sanity check. §2.5 is explicit: exact equality is the wrong bar for generation; the golden
  and drift gauges carry behaviour.

- **The three-process budget sum** (§2.3, inherited from bp-116) — *measures:* whether a prospective
  resident set fits `usable_ram_gb`. *valid when:* every per-process budget is measured at that
  role's actual ctx. *fails its keep if:* a tier's steady-state RSS diverges from its budget by
  >10% — then budgets are declarations again, which is finding-0174 in new clothes.

## 9. Non-goals

- ⚑ **No flip.** Every per-tier flip is the owner's (§2.6, §4).
- ⚑ **No model change.** Same models, matched quant. A quant mismatch is a model change (§3 Q2).
- **No Ollama retirement** — a separate owner decision after the deskcheck (§3 Q8).
- **No deletion of `OllamaClient` or `[ollama]`** — the standing rollback.
- **No fetching of models by the core** (§2.4).
- **No persona or prompt edits** to reconcile a template difference (§1.2) — fix the spawn, not the
  persona.
- **No writing to `eval/golden/**`** — foundation denylist.

## 10. Stop-and-raise conditions

- ⚑ **The re-entry condition does not hold** (V-B unresolved, or V-A unmeasured) ⇒ **do not start.**
  This is why the plan is parked; the front-matter `re_entry` is the gate.
- ⚑ **Item 1's falsifier fires** — prompt bytes differ, or quant differs ⇒ **STOP.** The first
  confounds every comparison; the second is a model change wearing a migration's clothes.
- ⚑ **Item 3's falsifier fires** — a tier does not fit even with the documented eviction ⇒ **STOP
  and return the note to the owner.** §2.9 says exactly this: the ctx budgets or the tier lineup
  must change, and that is a design decision.
- ⚑ **Any tier's golden gate is red or drift is anomalous** ⇒ **STOP at that tier.** §2.5: cutover
  is per-lane all-or-nothing, gated on measured equivalence. The already-flipped tiers stay; this
  one does not proceed.
- **V-H shows the SIGTERM wedge is worse on the pinned build** ⇒ raise; the grace default and the
  drain bound (bp-112) may need revisiting, which is a cross-plan question.
- **The owner-placed GGUFs are absent or ambiguous** ⇒ park the criterion, file, continue with
  nothing (this plan has no work that does not depend on them). Never block on the owner — but here
  the honest action is to remain parked, not to build against a guess.
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| V-B GGUF sourcing | owner action, outside the repo | ⚑ the plan's own re-entry gate |
| vendored binary vs pinned brew | pinned brew + build asserted at spawn | brew churn, or V-H |
| MLX A/B | parked by the owner (2026-07-22) | after P1's seam, on the owner's read |
| warm-spare chat workers | no — stop-then-spawn | V-A's cold-load breaks the responsiveness bar |
| Ollama retirement | not in this plan | all tiers flipped + owner deskcheck |

**Rejected alternatives, per row:**

- **V-B.** Rejected: *convert Ollama's blobs* — rewriting GGUF metadata to satisfy upstream's
  `rope.dimension_sections` check would produce a file whose provenance is neither Ollama's nor
  upstream's, and whose behaviour is unverified against either. Rejected: *have the core fetch
  them* — §2.4's tier-2 egress claim rests on the spawn argv containing no download flag; a
  fetching core would forfeit it.
- **Binary source.** Rejected: *auto-updating install* — that is the property the migration exists
  to remove (§2.6: *"Never auto-updated"*).
- **MLX.** Owner-parked (2026-07-22); the seam bp-115 built is what makes it a cheap later A/B, and
  adopting it is a separate decision with its own re-entry condition.
- **Warm spares.** Rejected: *spawn-ahead* — the note parks it; one worker, stop-then-spawn, is the
  simplest kill semantics.

## 12. Dependency & ordering summary

Items: **1 → 2 → 3 → 5**, with **4** parallel to Item 3 after Item 2.

**`depends_on: [bp-118]`** — the embedder must be cut over first (§2.6's deliberate ordering:
biggest win, smallest risk, provable), and this plan extends the same files
(`eval/runtime_equivalence.py`, `ops/lifecycle/launcher.py`, `core/models/manager.py`)
sequentially.

⚑ **PARKED. `status: proposed` with `re_entry` set — do not bless to `ready` until BOTH hold:**
1. **V-B** — upstream-convention GGUFs present, loading on the pinned build, quant lineage verified.
2. **V-A** — 27b/35b true RSS measured at role ctx (bp-116 Item 1), because §2.3's synthesis and
   stretch policy is unsized without it.

⚑ **This plan is what stands between "the runtime wave landed" and "the migration is complete."**
At bp-118's seal the honest statement is: *the embedder migrated (pending the owner's flip); the
chat tiers are parked on an owner-sourced prerequisite; Ollama is not retired.* Reporting the wave
complete without enumerating this is precisely the completion-claim failure the M2/K1 lesson
records (finding-0148).

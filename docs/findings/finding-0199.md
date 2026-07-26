---
type: finding
id: finding-0199
status: routed
created: 2026-07-25
updated: 2026-07-26
links:
  - core/models/loader.py                              # _resident: the unreconciled books
  - core/models/ollama_client.py                       # ps() exists; the loader never calls it
  - ops/lifecycle/launcher.py                          # :1094 — the ONLY ps() caller, a status line
  - config/defaults.toml                               # [resources]; default_keep_alive = "30m"
  - docs/findings/finding-0174.md                      # the sibling: the ceiling ignores the embedder
  - docs/design-notes/dn-supervision-and-liveness.md   # §2.7 flags the non-reconciliation
  - docs/brainstorms/local-model-runtime.md            # NEW NOTE 2 — where the durable fix lives
ftype: design
origin_plan: orchestrator
route: orchestrator
resolution: routed — re-entry SATISFIED on both clauses (note ratified + interim minted); the code defect is live until bp-107 lands
---

# The memory ceiling (non-negotiable #8) can be breached on the crash-restart path while its guard reports OK

> **Triage 2026-07-26 (session-52) — re-entry fired and discharged into plans; the code defect is
> unchanged.** `TwoSlotLoader` never reconciles `_resident` against Ollama: a repo-wide search finds
> **no `.ps()` caller in `core/models/loader.py` at all**, and the only production caller is the
> cosmetic embedder status line (`ops/lifecycle/launcher.py:1192` — drifted from the cited `:1094`,
> same role). `loader.py:33,77-78,83-86` still early-returns and evicts over an empty dict.
> **Discharge:** `dn-local-model-runtime` is `ratified` (`warrant:` this finding) and its §2.8 rules
> the interim fix be minted separately, *"NOW"* — that plan is **bp-107 (`ready`)**, with bp-116 the
> durable fix (residency becomes a kernel fact).
> **⚑ This finding's own "Status of the evidence" section is now STALE:** `bp-107/plan.md:49` records
> it was **REPRODUCED LIVE, all three phases** (corroborated `dn-local-model-runtime:112`).
> **Closure:** when `loader.py` reconciles against `ps()` before `_check_ceiling`. **Sequencing:**
> bp-107 must merge before bp-116 is spawned — both land on `core/models/loader.py`
> (`bp-115/plan.md:133` already records the de-confliction).

## What

`TwoSlotLoader._resident` (`core/models/loader.py:33`) is an **in-process dict that starts empty on
every construction**, and nothing anywhere reconciles it against what Ollama is actually holding.
`OllamaClient.ps()` exists (`ollama_client.py:78`) and is called from exactly **one** place in the
repository — `ops/lifecycle/launcher.py:1094`, the cosmetic embedder line in the `status` render.
**The accounting path never calls it.**

Ollama is a separate, long-lived process that outlives the supervisor. So belief and reality drift
in both directions, and one of them breaches the ceiling:

**False-absent (the breach).** A supervisor dies. Ollama keeps holding worker model A
(`default_keep_alive = "30m"`, `config/defaults.toml:10`) and the pinned model
(loaded with `keep_alive = -1` — *never* evicted by timer, `loader.py:88`). A new supervisor starts
with `_resident = {}`, believes nothing is loaded, and calls `ensure()` for worker model B:

- `_prospective` (`:44-55`) builds `{B}` — it can only reason over what this process loaded;
- `_check_ceiling` (`:57-69`) sums the **declared** `resident_gb` of `{B}` and **passes**;
- the eviction loop `for gone in [n for n in self._resident if n not in prospective]` (`:83-86`)
  iterates an **empty** dict, so nothing tells Ollama to drop A;
- `client.load(B)` lands B on top.

Ollama now holds pinned + A + B. The loader believes it holds one model. `max_resident_models`
and `usable_ram_gb` (`[resources]`, whose own comment says *"The loader refuses work that would
breach this (Invariant 8)"*) are both evaluated against the belief.

**False-resident (the quieter half).** `ensure()` early-returns on `if name in self._resident`
(`:77-78`). After Ollama's own 30-minute timer evicts a worker, the loader still claims it is
resident: it skips a load that is actually needed, and its ceiling arithmetic over-counts, refusing
admissible work.

## Why it matters

Non-negotiable **#8** is one of the inviolable kernel items: *"Respect the memory ceiling — ≤ 2
resident models, ~20–24 GB usable; the scheduler refuses breaching work."* A guard that checks a
belief it never reconciles is **advisory, not enforcing** — and it is silent about being wrong,
which is the precise shape the owner named as disqualifying: *"we do not want something that is
going to allow us to shoot ourselves in the foot without realizing."*

The reachability is what makes this urgent rather than theoretical: the breach lives on the
**crash-restart path**, which is exactly the path bp-105 just hardened, and which **launchd
`KeepAlive` exercises automatically and often**. The likeliest real trigger is an unclean exit
followed by an automatic restart inside the 30-minute keep-alive window.

Distinct from **finding-0174** (*the ceiling ignores the embedder* — an unaccounted consumer).
This is a different defect in the same class: the accounting is **unreconciled and starts from
zero**. Both point at the same structural claim — *the memory ledger is maintained by an actor
that cannot observe what it accounts for, and that a third party can invalidate unilaterally.*
That is the runtime-layer twin of `dn-supervision-and-liveness`'s
*"every ops ledger is written by the actor whose failure it must record."*

## Status of the evidence — read this before acting

**Code-traced, NOT empirically reproduced.** Every citation above was read; the breach sequence is
derived from the control flow, not observed on a live system. The audit's standing lesson is that
an overstated record is its own defect, so this is filed at the strength it actually has.

**The experiment that would settle it** (safe, ~10 minutes, daemon down): load a worker model via
Ollama directly, confirm with `ollama ps`, then construct a `TwoSlotLoader` in a fresh process and
call `ensure()` for a *different* worker model. Observe whether `ollama ps` then shows both, and
whether `_check_ceiling` raised. Do **not** run this against the live daemon.

## Candidate remedies (routing, not prescription)

- **Interim, builder-sized:** reconcile `_resident` against `ps()` at loader construction and/or
  before `_check_ceiling`. Cheap and closes the cold-start hole. Limitation to state plainly: `ps()`
  returns *names*, so a model absent from the registry cannot be costed — partial accounting, which
  is still strictly better than accounting from zero, but must not be reported as full.
- **Durable:** this is an argument for **NEW NOTE 2 (local-model-runtime, llama.cpp-direct)**. If
  the palace owns model loading, residency stops being a *belief about another process* and becomes
  a *fact we hold* — the false-absent and false-resident states become unrepresentable rather than
  detected, and no third-party eviction timer can invalidate the books. Ranked on
  `supervision-and-liveness`'s tier ladder this is the move from **tier 5** (runtime check against
  a belief) to **tier 1–2**.
- `dn-supervision-and-liveness` §2.7/§2.8 already flags the non-reconciliation and routes it to
  NEW NOTE 2; it does **not** draw out this cold-start breach. That is what this finding adds.

## Re-entry condition

Blocks nothing today — but the interim reconcile should be weighed **before** the restart, since
the restart is a fresh supervisor coming up against an Ollama that has been holding models since
run #35. Re-entry: when NEW NOTE 2 is passed, or sooner if the owner wants the interim reconcile
minted as a small plan.

---
type: build-plan
id: bp-116
track: ops
status: ready
design_ref:
  - docs/design-notes/dn-local-model-runtime.md
contract: builder
write_scope:
  - core/models/manager.py
  - core/kernel/config/loader.py
  - config/defaults.toml
  - ops/lifecycle/launcher.py
  - tests/unit/test_process_manager.py
  - tests/integration/test_runtime_wiring.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 350k
  actual: null
depends_on: [bp-115, bp-112]
parallelizable_with: []
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0174.md
  - docs/findings/finding-0199.md
  - docs/build-plans/bp-107/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0174.md
---

# Build Plan — P2: the process manager — residency becomes a kernel fact

## 0. Mode & provenance

**P2 of `dn-local-model-runtime` §2.6**: *"The process manager + accounting (§2.3, §2.4). Lands
flag-off beside the untouched `TwoSlotLoader`; the daemon keeps running Ollama until a role
flips."* This is where finding-0174 and finding-0199 are fixed **structurally** rather than
guarded: the embedder cannot exist except through the budget gate, and there is no belief dict left
to go stale.

⚑ **`TwoSlotLoader` is UNTOUCHED by this plan** — the note says so, and it keeps this plan off
bp-107's surface (the finding-0199 interim reconcile, landing on the same file). Two mechanisms
coexist until bp-118 flips a role; that coexistence *is* the rollback story.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.

## 1. Objective

The palace owns local model residency: a model is resident iff a child process we spawned is alive,
and no spawn happens except through a budget gate seeded from measured RSS.

### 1.2 Non-goals (explicit — see §9)

Not a cutover (bp-118/bp-119 — the defaults still route everything through Ollama). Not the
equivalence harness (bp-117). Not touching `TwoSlotLoader`. Not a model change (owner-stated).

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-local-model-runtime.md` — **§2.1 in full** (the measured ground: A–G),
   **§2.3** (the three-process residency model), **§2.4** (the seal boundary and the manager),
   §2.7 (the tier ledger), §2.9, **V-A, V-C, V-D, V-F** — the content spec
2. `docs/build-plans/bp-115/plan.md` §6 — the `InferenceClient` protocol and `[runtime]` schema
3. `docs/findings/finding-0174.md` and `finding-0199.md` — the two warrants
4. `docs/build-plans/bp-107/plan.md` — the interim guard this plan eventually retires; **read it
   to be sure this plan does not pre-empt or contradict it**
5. `core/models/loader.py` — **read, do not edit.** The behaviour being superseded
6. `core/sandbox/runner.py:55-93` — the in-repo subprocess+timeout+destroy precedent
7. `core/sealing.py` — the per-process monkeypatch and its native-extension caveat
8. `ops/lifecycle/launcher.py:420-435` — where model components are built today

**Does core already have this?** `core/sandbox/runner.py` owns subprocess lifetime for *untrusted*
code and is the discipline to borrow — argv, timeout, destroy-on-expiry — **not** code to copy.
`core/typedshims/psutil.py` already exists for process introspection (`process_rss` at `:31`); use
it rather than importing `psutil` raw. ⚑ bp-106's warrant is precisely that a raw `import psutil`
passed every gate; the one-file rule for third-party imports binds here.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — is the "two slots" model even real?** ⚑ **No — measured.** §2.1 D: `pgrep` during the
  design pass showed `/Applications/Ollama.app/Contents/Resources/llama-server`, **one subprocess
  per loaded model**, `-np 1`, the 2b at `-c 8192 --no-jinja --chat-template chatml`, the embedder
  at `-c 40960 --embedding`, both `--offline`. Reality is N single-model servers behind an opaque
  Go manager. **The migration replaces the manager, not the server** — a far smaller change than
  "swap the inference engine", and the plan must be scoped accordingly.
- **Q2 — how much does the embedder actually cost?** ⚑ **10.0 GB, not 2.5.** §2.1 C: under Ollama
  at its model-default ctx 40960 the embedder is 10.0 GB, because `OllamaClient.embed()` passes no
  `num_ctx` (`core/models/ollama_client.py:97-104`, verified). Under palace-launched `llama-server`
  at ctx 8192 the same blob is **RSS 3.69 GB**. finding-0174 is 4× worse than filed, and the
  mechanism is *context, not weights*.
- **Q3 — why is a weights-only `resident_gb` the wrong shape?** Because Q2's gap is ctx-driven.
  `ModelConfig.resident_gb` (`core/kernel/config/loader.py:302`) is a declared constant, and
  `[embedding]` (`config/defaults.toml:105-119`) declares **none at all** — the embedder is absent
  from `core/models/registry.py` entirely. §2.3's replacement is per-process budgets = weights +
  ctx-dependent buffers, **seeded from measured bring-up RSS and reconciled against live RSS**.
- **Q4 — is ctx 8192 safe for embedding?** **V-D, and it must be confirmed, not assumed.** Chunks
  are capped at `max_chars = 1200` (`config/defaults.toml:109`), far under 8k tokens, and the
  query path wraps a single query (`core/ingest/embed.py:31-34`). But *confirming no palace embed
  call can exceed it* requires checking both paths. Fail-closed helps: the typed
  `exceed_context_size_error` is loud (§2.1 G).
- **Q5 — what are the big-tier numbers?** ⚑ **Unknown — this is V-A, and it blocks §2.3's policy.**
  The design pass could not measure 27b/35b: the 14.4 GB free-RAM envelope forbade it. Steady-state
  routine is 2.5 + 3.7 + 6.2 ≈ 12.4 GB, but synthesis @32k and stretch likely do **not** fit
  beside both housemates. Item 1 measures; §10 makes "they do not fit even with the embedder
  stopped" a STOP that returns the note to the owner (§2.9's own falsifier).
- **Q6 — why is SIGTERM→grace→SIGKILL required rather than nice-to-have?** ⚑ **Measured.** §2.1 G:
  llama-server **wedges on SIGTERM mid-request** — no exit in 30.9 s in one observation, >3.5 min
  in another; SIGKILL required. Idle SIGTERM is 0.25 s. A graceful-only stop hangs the manager.
- **Q7 — is SIGKILL of an inference server safe?** **Yes, by construction** (§2.4): it is stateless
  — no store handles, no corpus writes; the only loss is in-flight tokens, which the compute/land
  split already treats as disposable.
- **Q8 — does the seal boundary move?** **No.** §2.4: spawned servers, never in-process bindings.
  `core/sealing.py` is a per-Python-process monkeypatch whose own docstring names native extensions
  as the bypass, so `llama-cpp-python` *inside* the core would put a large C++ surface where the
  guard cannot see it — it would **weaken** the provable seal. The inference server is outside the
  seal **by design**, exactly as Ollama is today.
- **Q9 — can anything reach tier 1?** **No, and one row explains why** (§2.2, §2.7): jetsam and
  process crash are external actors, so "resident set changed without our decision" stays
  representable. It is *detected* at tier 3 (waitpid), not made impossible. The code comments must
  say tier 3, never tier 1.

**Additional risks or questions surfaced during reading:**

- ⚑ **The embedder is the one blob that is portable** (§2.1 E). Chat blobs fail to load upstream
  (`qwen35` arch, `rope.dimension_sections` expected 4, got 3). So this plan can bring up a real
  embedder server but **cannot bring up a real chat server**; V-B (owner-fetched upstream GGUFs)
  gates that and belongs to bp-119.
- `ops/lifecycle/launcher.py` is the wave's contended file. This plan touches it only for
  component construction, and must be sequenced after bp-112 (§12).
- Item 1's measurements need real memory headroom. Run them with the daemon **down** and record
  the free-RAM envelope alongside each number, or a later reader cannot tell a measurement from an
  artefact of pressure.

## 4. Reconciliation  <!-- Part B -->

- **`core/models/loader.py:1-16`** — the module docstring's *"Two slots, never more"* →
  **banner: correction**, but written **in the new module**, not in `loader.py` (which stays
  untouched, §0). `core/models/manager.py`'s docstring must state plainly that it supersedes the
  two-slot model, why (§2.1 D: the two-slot server does not exist), and that the loader remains the
  live path until a role flips.
- **`config/defaults.toml:19-27`** — the `[resources]` comment block, which describes
  `resident_gb` as *"the weights footprint; KV-cache (bounded per role by num_ctx) is additional
  headroom, accounted as a refinement in a later phase"* → **banner: correction.** That later phase
  is this one, and the measured gap (Q2) is 4×, not a refinement. Correct the comment where the new
  budgets are defined; **do not delete `max_resident_models`** — the loader still reads it
  (`core/models/loader.py:59`) and deleting it breaks the live path.
- **`docs/findings/finding-0174.md` / `finding-0199.md`** → **cross-ref: extension.** Both are
  fixed structurally here, but neither closes until a role actually flips (bp-118). A builder may
  not edit a finding; record the evidence in the journal for the orchestrator.

## 5. Write scope

`core/models/manager.py` (new) is the whole production surface for Items 2–4: spawn, health,
budget gate, stop ladder, residency view. `core/kernel/config/loader.py` + `config/defaults.toml`
carry the per-role budget/ctx keys that extend bp-115's `[runtime]` section.
`ops/lifecycle/launcher.py` carries **component construction only** — so the ON switch exists
(wiring is part of finishing) even though the default leaves the manager unconstructed. Two new
test files.

⚑ Deliberately OUT of scope, each for a stated reason:
- **`core/models/loader.py`** — §2.6 P2 says it stays untouched; it is also bp-107's surface.
- **`core/models/registry.py`** — the embedder's absence from it is finding-0174's *symptom*; this
  plan fixes the cause by putting residency in the manager, and re-costing the registry is bp-118's
  cutover concern.
- **`scheduler/supervisor.py`** — bp-110/bp-112 own it; the dispatch-time ceiling gate
  (`supervisor.py:71`) keeps calling the loader until a role flips.
- `eval/golden.py`, `eval/golden/**` — foundation denylist. Every design note.

## 6. Interfaces pinned inline

**The three-process residency model** (`dn-local-model-runtime` §2.3 — footprints measured
2026-07-25, M2 Max 32 GB, against Ollama 0.31.2 and llama.cpp b10090):

| process | model | ctx | grounded footprint |
|---|---|---|---|
| pinned router | qwen3.5:2b | 8192 | 2.5 GB (measured, `ollama ps` @8k) |
| worker (one at a time) | per tier | per role | 9b @16k = 6.2 GB measured; 27b/35b = V-A |
| embedder | qwen3-embedding:4b | 8192 | 3.69 GB RSS measured (was 10 GB @40960) |

**Residency, verbatim from §2.3 — the sentence the whole plan implements:**

```
Residency is process existence. A model is resident iff its server process is alive. The loader's
successor (the process manager) holds child handles; resident_models() becomes a view over the
process table. The false-absent and false-resident states of finding-0199 lose their
representation: there is no belief dict to start empty or to go stale.
```

**⚑ The spawn argv IS the capability** (§2.4, tier 2). What is present and what is absent both
matter:

```
PRESENT:  -m <local path>      --host 127.0.0.1     -c <role ctx>     --offline
ABSENT:   --model-url          -hf                  any download flag whatsoever
```

Model acquisition is an owner/ops action outside the core, exactly as `ollama pull` is today. The
server is never *given* anything to dial out for.

**The stop ladder — required, not optional** (§2.1 G measured the wedge):

```
SIGTERM -> wait grace_s -> SIGKILL -> waitpid
(idle SIGTERM measured 0.25 s; mid-request SIGTERM did NOT exit in 30.9 s, and >3.5 min in a
 second observation. A graceful-only stop hangs the manager.)
```

**The manager's surface:**

```python
@dataclass
class ProcessManager:
    """Palace-owned local inference processes. The ONLY spawner (tier 2), so the budget gate
    cannot be bypassed; residency is read from the process table (tier 3). Nothing here reaches
    tier 1 — jetsam and crashes keep 'the resident set changed without our decision'
    representable; they are DETECTED at tier 3, not made impossible (§2.2, §2.7)."""

    def ensure(self, role: str) -> Server: ...      # budget-gated spawn, readiness-gated handoff
    def stop(self, role: str) -> None: ...          # SIGTERM -> grace -> SIGKILL -> waitpid
    def resident(self) -> list[Resident]: ...       # a VIEW over live children, never a belief
    def reconcile(self) -> None: ...                # live RSS vs budget; alarms on >10% divergence
```

**The budget gate — the refusal point that must survive** (non-negotiable #8). `_check_ceiling`'s
*refusal before load* survives; only its inputs change from declared constants to measured budgets:

```
sum(per-process budget) over the PROSPECTIVE set  >  usable_ram_gb   =>  refuse, before spawning
per-process budget := measured bring-up RSS at the role's ctx (seeded), reconciled against live ps
```

⚑ **`max_resident_models = 2` is REPLACED, not reinterpreted** (§2.3): the constraint becomes "the
budget sum fits" plus a policy row per role. **But the config key stays** —
`core/models/loader.py:59` still reads it and the loader is the live path until bp-118.

**Steady state and the eviction policy** (§2.3): routine = 2.5 + 3.7 + 6.2 ≈ 12.4 GB. Synthesis
@32k and stretch likely do not fit beside both housemates (V-A measures); the manager stops the
embedder — and for stretch, the pinned router — for the window, restarting after. **That is the
same `evicts_pinned` semantics the loader already documents, now executed by an actor that can
verify it happened.**

## 7. Items

Blast radius: measurement → an isolated manager → the ratchets → wiring that constructs nothing by
default.

### Item 1 — V-A, V-C, V-D: the numbers the design's policy rests on

- **Objective:** the budgets are measured on this machine, not carried from the design pass.
- **Files:** none (scratchpad; results in `journal.md`)
- **Acceptance test:** journal records, with the free-RAM envelope beside each figure:
  **V-A** — 27b (and 35b if it fits) under llama-server: upstream-GGUF bring-up time and true RSS
  at the role ctx. **V-C** — `lsof` across load + serve + `--offline`, showing loopback-only
  sockets. **V-D** — confirmation that no palace embed call can exceed ctx 8192 (chunker cap
  `max_chars = 1200` **and** the query path), and that the typed overflow error surfaces loudly if
  one does.
- **Falsifier:** ⚑ *V-A shows synthesis/stretch cannot fit even with the embedder stopped.* That is
  §2.9's own named falsifier — the ctx budgets or the tier lineup must change and **the note
  returns to the owner** (§10). ⚑ *V-C shows any non-loopback socket* — the tier-2 egress claim is
  false and §2.4 needs revisiting before anything ships.
- **Invariant(s) it must not violate:** run with the daemon down; unload everything afterwards
  (the design pass's hygiene); measure, do not tune.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — the manager: spawn, health, stop

- **Objective:** a palace-owned llama-server can be started, waited for, and reliably killed.
- **Files:** `core/models/manager.py`, `tests/unit/test_process_manager.py`
- **Acceptance test:** `ensure("embedder")` spawns with the §6 argv, waits `/health` 503→200, and
  serves; `stop()` follows SIGTERM→grace→SIGKILL and **reaps** (waitpid returns) even against a
  process mid-request; `resident()` reflects the process table, and a child killed externally
  disappears from it **without any bookkeeping call**.
- **Falsifier:** ⚑ *`resident()` can disagree with the process table.* If any cached dict can go
  stale, finding-0199 has been rebuilt one layer up — that is the entire point of the plan. ⚑ Also:
  *a wedged server survives `stop()`* (§2.1 G's measured wedge is the reason the ladder exists).
- **Invariant(s) it must not violate:** the manager is the **only** spawner; argv carries no
  download flag; `--host 127.0.0.1` literal, never a hostname; `psutil` is reached only through
  `core/typedshims/psutil.py` (bp-106's one-file rule).
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — the budget gate, seeded from measurement

- **Objective:** no spawn happens that would breach non-negotiable #8, and the embedder is inside
  the books by construction.
- **Files:** `core/models/manager.py`, `core/kernel/config/loader.py`, `config/defaults.toml`,
  `tests/unit/test_process_manager.py`
- **Acceptance test:** a spawn whose prospective budget sum exceeds `usable_ram_gb` **raises before
  spawning**; the embedder is counted (it cannot exist except through the gate); `reconcile()`
  alarms when live RSS diverges from the seeded budget by more than 10%.
- **Falsifier:** ⚑ *steady-state RSS diverges from the spawn-time budget by >10%* (§2.9's falsifier
  verbatim). Then budgets are declarations again — finding-0174's defect in new clothes — and the
  reconcile loop must alarm rather than the plan claim success.
- **Invariant(s) it must not violate:** the refusal is **before** the spawn, never after; the
  arithmetic check is reported as **tier 5 with a tier-4 ratchet**, never as tier 1 or 2 (§2.7 —
  overclaiming is the note's named foot-gun); `max_resident_models` stays in config for the loader.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — the tier-4 ratchets

- **Objective:** the egress and sole-spawner claims are proven mechanically.
- **Files:** `tests/unit/test_process_manager.py`, `core/models/manager.py`
- **Acceptance test:** (a) a test asserting the spawn argv contains **no download flag** and does
  contain `--host 127.0.0.1` and `--offline`; (b) an `lsof` scan asserting the server holds
  loopback-only sockets while serving; (c) a source/AST scan asserting **no spawn site outside the
  manager** (the `check_imports.py` species, §2.3).
- **Falsifier:** ⚑ *adding `--model-url` to the argv leaves the argv ratchet green*, or *adding a
  second `subprocess.Popen` of the server binary elsewhere leaves the sole-spawner scan green.*
  Plant both mutations. The scan must catch a **function-local** spawn, not only a module-level one
  — bp-106 Item 4 records that a module-level-only AST walk reproduces the hole exactly.
- **Invariant(s) it must not violate:** the ratchets run in the local CI gate; the tier claim in the
  code comment is **4**, stated as such.
- **Touches stored data?** No. **Parallelizable?** Yes, with Item 3. **Depends on:** Item 2.

### Item 5 — the ON switch exists, and is off

- **Objective:** the daemon can construct the manager from config, and does not by default.
- **Files:** `ops/lifecycle/launcher.py`, `tests/integration/test_runtime_wiring.py`
- **Acceptance test:** with defaults, the daemon builds **exactly today's components** and no
  llama-server is spawned (assert no such process exists after a start/stop cycle); with
  `[runtime] embedding_backend = "llamacpp"` and a configured `server_binary`, the manager is
  constructed and health-gated at startup. Preflight reports the manager's state honestly when
  configured.
- **Falsifier:** ⚑ *the feature ships un-runnable* — the config key exists but nothing constructs
  the manager, so flipping it does nothing. That is the code-ingest lane's Plan-B lesson (owner,
  2026-07-22): flag-off is not the same as unwired, and the ON switch is part of the deliverable.
- **Invariant(s) it must not violate:** default behaviour is byte-identical; `TwoSlotLoader` is
  still constructed and still the live path; a missing/misconfigured `server_binary` **fails
  loudly at startup**, never silently falls back (a silent fallback would make a failed cutover
  look like a successful one).
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Items 3, 4.

## 8. Math carried explicitly

- **Per-process memory budget** — *measures:* the resident cost of one model server at a given
  context, as weights + ctx-dependent buffers. *valid when:* the budget is **seeded from measured
  bring-up RSS at that exact ctx** and reconciled against live RSS; ctx is fixed per role.
  *fails its keep if:* steady-state RSS diverges from the budget by >10% (§2.9), or if a role's
  ctx changes without re-measuring — at which point it is a declaration again, which is exactly
  finding-0174.

## 9. Non-goals

- **No cutover.** Defaults route through Ollama; the flip is the owner's at bp-118.
- **No touching `TwoSlotLoader`** (§2.6 P2) or `core/models/registry.py` (§5).
- **No chat-server bring-up** — the chat blobs do not load upstream (§2.1 E); V-B gates it (bp-119).
- **No in-process bindings** (`llama-cpp-python`) — it would weaken the provable seal (§2.4, Q8).
- **No tier-1 claims anywhere** (§2.7, Q9).
- **No re-embed, no model change, no σ recalibration** — `dn-local-model-runtime` §1.2.
- **No raw `import psutil`** — `core/typedshims/psutil.py` only (bp-106's warrant).

## 10. Stop-and-raise conditions

- ⚑ **V-A shows synthesis/stretch cannot fit even with the embedder stopped** ⇒ **STOP and raise.**
  §2.9 says this returns the note to the owner: the ctx budgets or the tier lineup must change, and
  that is a design decision, not a builder's.
- ⚑ **V-C shows a non-loopback socket in a serving llama-server** ⇒ **STOP.** §2.4's tier-2 egress
  claim would be false, and this touches the sealed core's inference boundary.
- ⚑ **A model's memory outlives its process** (RSS/Metal allocations persisting after waitpid) ⇒
  **STOP.** §2.9's first falsifier; the entire residency-equals-process-existence model would be
  wrong.
- **`stop()` cannot kill a wedged server** (an unkillable state) ⇒ STOP and file; the escalation
  contract has no teeth and §2.1 G's measurement was optimistic.
- **The budget gate would refuse the pinned router in a reachable configuration** ⇒ STOP. Same
  shape as bp-107's brick risk: a memory guard that becomes an availability outage.
- **A raw third-party import proves necessary** ⇒ STOP (bp-106's one-file rule).
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| vendored binary vs pinned brew | pinned brew + build asserted at spawn | brew churn, or V-H |
| warm-spare workers | no — stop-then-spawn | V-A's cold-load breaks the responsiveness bar |
| embedder always-on vs on-demand | always-on at 3.7 GB | V-A's synthesis arithmetic |
| jetsam behaviour | detected at tier 3, reported | V-F measures it under real pressure |
| embed ctx | 8192 (from the model default 40960) | V-D finds a call that can exceed it |

**Rejected alternatives, per row:**

- **Binary source.** Rejected: *auto-updating install* — that is the exact property Ollama.app has
  and the migration exists to remove (§2.6: *"Never auto-updated"*). A bump must be a deliberate ops
  action that re-runs the equivalence gate.
- **Warm spares.** Rejected: *spawn-ahead* — the note parks it; one worker with stop-then-spawn is
  the simplest kill semantics and matches the sandbox's "overran ⇒ discarded, never reused".
- **Embedder residency.** Rejected: *on-demand* — 3.7 GB fits beside routine and the router
  (§2.3's steady state), and repeated bring-up would cost ~1–3 s per ingest batch.
- **Jetsam.** Rejected: *claim tier 1* — an actor outside our scheduler can still change residency,
  which bars a tier-1 claim anywhere in the note (§2.2). What we get is that it is *observed*
  (waitpid) instead of silently absorbed into a stale belief.
- **Embed ctx.** Rejected: *keep the model default* — that is the 10 GB figure and the largest
  single accounting win available (~6.3 GB, §2.1 C).

## 12. Dependency & ordering summary

Items: **1 → 2 → 3 → 5**, with **4** depending only on Item 2 (build the ratchets early; they are
what make the claims true).

**`depends_on: [bp-115, bp-112]`:**
- **bp-115** — substantive: the manager serves roles through the `InferenceClient` seam and extends
  the `[runtime]` section bp-115 defined.
- **bp-112** — file contention, stated honestly: `ops/lifecycle/launcher.py` is the wave's
  contended file (bp-108 → bp-111 → bp-112 → **bp-116**, strictly sequenced). This plan touches it
  only for component construction, but a concurrent worktree would still conflict.

**Not parallelizable with anything.** **bp-117 depends on this plan** — the equivalence harness
spawns its llama-server *through the manager* rather than re-implementing spawn logic in `eval/`,
which is a DRY requirement, not a convenience.

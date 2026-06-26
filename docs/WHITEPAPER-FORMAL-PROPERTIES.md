# The Mind Palace — Verifiable Properties, Proof Obligations & Exposed Gaps
### Formal companion II to `WHITEPAPER.md` / `WHITEPAPER-TECHNICAL.md`

This document turns the design's invariants into a **verification plan**: each is stated
formally, classified by *how strongly it can be guaranteed*, and paired with the obligation that
discharges it. It also records the **gaps formalization exposed** — the real payoff.

## The honest boundary
Formalization here buys **specification precision**, **verifiable properties**, and
**gap-surfacing**. It does **not** buy end-to-end proof: LLM output quality, native/OS code, and
hardware are **assumption-bounded**, not provable. The strongest assurance is *structural* —
the wrong state cannot be constructed — which needs no test at all.

### Assurance hierarchy (push every invariant as high as it goes)
1. **Structural / unrepresentable** — illegal state cannot be built (typed handle/view). *Proof = construction.*
2. **Static-checkable** — provable without running (import graph, signatures). *CI lint.*
3. **Runtime guard** — checked, fail-closed, before the dangerous act. *Assertion + test.*
4. **Property-tested** — invariant asserted over generated inputs. *Hypothesis/QuickCheck.*
5. **Assumption-bounded** — only boundable, with stated assumptions. *Documented limit.*

---

## Invariant catalog (the verification plan)

Let $\mathsf{Core}$ be the core module set, $\mathsf{Net}$ the network-capable modules,
$\to$ the import relation, $\mathcal{A}(\cdot)$ authority, $\rho$ provenance, $\mathsf{MR}$ the
mirror-readable classes, $\pi_{\mathsf{MR}}$ the mirror projection.

| # | Property (formal) | Tier | Discharge / obligation |
|---|---|---|---|
| I1 | egress: $\forall$ connect from core, $\mathrm{dst}\in\{\text{loopback},\text{AF\_UNIX}\}$ | guard + **assumption** | live test (external blocked) **+ stated assumption**: a native ext. opening its own socket bypasses a Python hook ⇒ OS isolation (pf/netns) is the real bound |
| I2 | no core→network path: $\nexists\,\text{path}\ \mathsf{Core}\!\to^{*}\!\mathsf{Net}$ | **static** | import-graph lint in CI (core may not import edge/sockets/http) — *promote from runtime to static* |
| I3 | model advises: no callsite executes model output as code/shell/cred outside the gate | **structural** + test | `Agent.respond` returns data, has no action path; dispatcher is the sole action path |
| I4 | sandbox powerless: $\mathcal{A}(\text{exec})\cap\{\text{net},\text{vault},\text{cred}\}=\varnothing$ | **structural** + guard | container `--network=none`, no mounts; integration test code can't reach net/vault |
| I5 | interpreted unforgeable: $\forall x\ \text{via DerivedStore},\ \rho(x)=\textsf{interpreted}$ | **structural** | by construction — *no provenance parameter exists* (exemplar of unrepresentable) |
| I6 | firewall: $\mathrm{in}(\Omega)\subseteq\pi_{\mathsf{MR}}(V)$ for introspective $\Omega$ | **prefilter (convention)** → promote | property test (observed never returned to mirror) **and** introduce a typed `MirrorView` so a non-MR view is *untypable* ⇒ structural |
| I7 | Constitution outermost: $\mathrm{frame}[0]=\textsf{Constitution}$, $\forall$ agents | structural + test | `frame_context` prepends; fingerprint test (exists) |
| I8 | ceiling: $\sum_{R}m\le C\ \wedge\ |R|\le2$ | guard + **FSM** | check-before-load; loader is a tiny FSM ⇒ *exhaustively checkable* |
| I9 | grounding: $\textsf{grounded}(A)\iff\mathrm{Cit}(A)\subseteq\mathrm{Ret}$ | property-test | Hypothesis: random answers w/ in- and out-of-set citations ⇒ predicate matches (**needs stable citation IDs — gap G1**) |
| I10 | recursion: $c(\kappa)\le\gamma^{d(\kappa)}g(\kappa)$, authored leaves only | property-test | Hypothesis over synthetic derivation DAGs ⇒ $c$ non-increasing in $d$; reject cycles (**needs persisted derivation edges — gap G2**) |
| I11 | belief ≠ utility: no $f$ maps $(c,u)\mapsto$ one ranking scalar | **structural** | two disjoint ranking APIs; review/test there is no combiner |
| I12 | gate: $s'=\Delta\!\cdot\!s$ iff $G(\Delta,s)$ else $s$; $\Delta$ never self-applies | structural + guard + **FSM** | only code applies $\Delta$; gate is a tiny FSM ⇒ checkable (**$\textsf{conforms}$ conjunct deferred — gap G5**) |
| I13 | authority non-widening: $\mathcal{A}(\text{agent}\oplus\varsigma)=\mathcal{A}(\text{agent})$; $\mathcal{A}(\mathrm{mint})=\mathrm{scope}\cap\textsf{MAX}$ | **structural** + test | skills add context not handles; dispatch table = held handles; property test over arbitrary skill composition |

The table **is** the build target: every row is either already structural (I3,I5,I11,I13), or names the
test/lint/promotion that discharges it.

---

## Safety vs liveness

**Safety** $\;\square\neg\text{bad}\;$ (enforce structurally): I1–I8, I11–I13 — the firewall holds, the
core never egresses, the gate never applies an unapproved/regressing change, the ceiling is never
exceeded, a fabricated answer never ships, authority never widens.

**Liveness** $\;\lozenge\,\text{good}\;$ (needs the supervisor's progress guarantees):
- every proposed change is *eventually* validated-or-rolled-back;
- $D(t)>\Theta$ *eventually* raises an alarm;
- a degraded router *eventually* falls back to rules;
- queued jobs *eventually* run.

The last is the dangerous one: under a perpetual foreground gate, low-priority cron (dreaming,
curation) can **starve**. Safety is free under the gate; liveness is not — **gap G6** below.

---

## Composition & non-interference (what survives putting pieces together)
- **Zone non-interference.** I2 is a property of the *import closure*: if $\mathsf{Core}\not\to^{*}\mathsf{Net}$, no egress path exists **regardless of edge behavior** — composition cannot create one.
- **Authority monotonicity.** I13 is closed under composition: no sequence of skill/role additions raises $\mathcal{A}$ above $\mathrm{scope}\cap\textsf{MAX}$.
- **Provenance preservation.** $\rho$ is assigned at ingest and is *invariant under all downstream derivation*; the only mutator is the human promotion $\uparrow$. So no pipeline stage can launder $\textsf{observed}$ into $\textsf{authored}$.

---

## What formalization exposed (the payoff — pin these before hardening)
*Status tags added by the 2026-06-26 hardening pass (see "Discharge status" below).*
- **G1 — Citation identifier scheme. [CLOSED]** $\mathrm{Cit}(A)\subseteq\mathrm{Ret}$ is only *decidable* with stable IDs. Decide: cite by content **digest** (or a stable note ID), never by fuzzy title. Until then I9 is ill-posed. → `core.selfcheck.Source` (title + stable digest); grounding resolves each citation to a single retrieved digest, and a title matching *two* digests is now flagged ambiguous instead of silently accepted. Librarian + dreamer pass `Source`s.
- **G2 — Persisted derivation edges + acyclicity. [CLOSED]** $d(\kappa)$ and the decay I10 are *uncomputable* unless each interpreted node records its scaffolding refs and the DAG is acyclic. Add a `derived_from` edge set; enforce acyclicity on insert. → `DerivedStore.add(derived_from=…)` records edges and **refuses a cycle at insert** (`DerivationCycleError`); `DerivedStore.depth` computes $d(\kappa)$; `core.recursion.decay_bound` gives $c\le\gamma^{d}g$.
- **G3 — Typed `MirrorView`. [CLOSED]** I6 is currently a call-site convention (pass `MR`). Introduce a `MirrorView` type the dreamer consumes, constructible *only* from $\pi_{\mathsf{MR}}$, so handing it observed data is a *type error* — promoting I6 from property-tested to structural. → `core.mirror.MirrorView`: sole constructor `project` applies $\pi_{\mathsf{MR}}$, and `__post_init__` raises on any non-authored row, so a non-MR view is **unrepresentable**. Dreamer + curator introspective reads go through it.
- **G4 — Drift metric & tolerance. [OPEN — Phase 11]** $D(t)=d(\mu(s_t),B)$ needs a concrete *normalized* metric over a mixed profile (rates ⊕ conformance vector) and a chosen $\Theta$. Specify the metric and band before the Phase-11 gauge. *Out of scope for this pass; still open.*
- **G5 — The gate's deferred conjunct. [STATED]** $G$ includes $\textsf{conforms}(\cdot)$, but the subjective judge is deferred. State the **live** guard honestly: $G_{\text{now}}=\textsf{approved}\wedge\text{golden}\ge B\wedge D\le\Theta$ (no $\textsf{conforms}$ yet). Do not let the formula overclaim. → `ops.gate.gate_admits(GateDecision)` encodes exactly $G_{\text{now}}$; `conforms` is **absent, not stubbed true**; FSM-checked over all 8 states. (The apply/validate/rollback loop that *uses* it is Phase 10.)
- **G6 — Cron liveness / anti-starvation. [CLOSED]** Add an aging policy (priority floor that rises with wait time) so background work *eventually* runs under sustained foreground use. Otherwise dreaming/curation can starve indefinitely — a silent liveness failure. → `scheduler.queue.AgingPolicy`: a QUEUED job's effective priority improves with wait time up to the INTERACTIVE floor (never preempting a REACTIVE escalation); a no-op under normal load.
- **G7 — Free parameters. [DECLARED]** $\gamma,\lambda,\sigma,k,h$ are unset. Declare bounds/calibration (e.g. $\gamma$ small enough that depth-3 is clearly subordinate; $\sigma$ tuned on the real corpus), not magic numbers. → γ,λ in `core.recursion` (γ=0.5 ⇒ depth-3 ≤ 0.125·g; λ≤0.25); σ = `dreaming.similarity_threshold` ∈ [0.55,0.75] (corpus-calibrated); k ∈ [3,8] (`Librarian.k`); h = `DEFAULT_REPLY_RESERVE` ∈ [512,2048]. Each declared at its site with a bound.
- **G8 — Don't over-formalize. [RETIRED]** The provenance preorder $\preceq$ is asserted but only the *set* $\mathsf{MR}$ is load-bearing today. Either use the ordering somewhere real or drop the claim — formalism should constrain, not decorate. → **Dropped.** Only $\mathsf{MR}$-membership and derivation-invariance of $\rho$ are load-bearing, and both are now *structural* (`MirrorView`; `DerivedStore` with no provenance param). The preorder is removed from the model (`core/provenance.py`, WHITEPAPER-TECHNICAL §provenance).

## Newly-exposed gaps (this hardening pass)
Formalization-by-implementation surfaced three residuals — recorded, not papered over:
- **G9 — Authored-leaf check is by-convention, not structural.** `DerivedStore` enforces *acyclicity* structurally, but it cannot tell an authored note digest from an arbitrary string, so "every support-closure leaf is authored" (I10's hard constraint) rests on the dreamer/curator *passing* authored digests. A structural check would have the store validate leaf refs against the raw/vector store on insert. Acceptable today (only those two callers write edges, and recursive dreaming is flag-OFF); revisit before enabling interpreted-on-interpreted derivation.
- **G10 — Grounding surface form is still a title.** I9 is now *decidable* (titles resolve to stable digests, collisions flagged), but the model still emits `[[title]]`, not `[[digest]]`; decidability holds exactly when titles are unique within $\mathrm{Ret}$ (now detected when they are not). Making the model cite digests directly would be fully structural but harms readability — a deliberate UX tradeoff, left as-is.
- **G11 — `MirrorView` guards the data, not the handle.** I6 is structural for the *introspective read path* (clustering consumes a `MirrorView`), but an agent still holds a reference to the full `VectorStore` and could call `all_rows()` directly. The guarantee is "the data that reaches introspection is provably authored," not "the agent cannot name the store." Tightening would inject only a `MirrorView`-source into the dreamer/curator.

---

## Discharge status (hardening pass, 2026-06-26)
Verification-only pass (no main-build advance; dream R&D flag OFF; runtime behavior unchanged).
Per invariant, what now discharges it and the **honest** residual. An invariant is not called
"verified" where it could be made structural — the residual is recorded instead.

| # | Tier now | What discharges it | Honest residual |
|---|---|---|---|
| I1 | runtime guard + **assumption** | `core.sealing` fail-closed loopback-only guard; live test | A native ext opening its own socket bypasses the Python hook ⇒ **OS isolation (pf/netns) is the real bound**; deployment-time, documented in `runbook.md §Sealing`. Not promotable in-process. |
| I2 | **static** (promoted) | `ops.import_lint` AST scan in CI + `tests/test_import_firewall.py`: core imports no `edge`/`cloud` (zero-exception) and no networking primitive outside the audited loopback allowlist (`sealing`, `ollama_client`) | None for the zone rule. Networking-primitive rule is "exactly these two audited files", honestly stated (not "no core http"). |
| I5 | structural | `DerivedStore.add` has no provenance param (test asserts) | — |
| I6 | **structural** (promoted) | typed `MirrorView` — non-MR view unrepresentable; dreamer+curator read through it; Hypothesis property | **G11**: guards the data, not the store handle. |
| I8 | guard + **FSM-verified** | `tests/test_loader_fsm.py` enumerates every reachable resident set (real + tight budget); ceiling holds in all; refuse-iff-breach | — |
| I9 | runtime-guard + **property-tested**, decidable | digest-backed `Source`; `check_grounding` resolves to a unique digest; Hypothesis | **G10**: surface citation is still a title (decidable iff unique in Ret; non-uniqueness now flagged). Not structural by nature (free-text output). |
| I10 | **structural acyclicity** + property-tested | `derived_from` + cycle-refused-at-insert; `depth`; `decay_bound` non-increasing (Hypothesis) | **G9**: authored-leaf-only is by-convention; the *adjudicator* that consumes the decay ranking is Phase 9 (not built). |
| I12 | decision **FSM-verified**; Δ-never-self-applies structural | `ops.gate.gate_admits` = $G_{\text{now}}$ (conforms deferred, honest); `tests/test_gate_fsm.py` | The apply/validate/rollback loop + `conforms` judge + drift metric (**G4**) are Phase 10/11. Only the *decision core* is verified. |
| I13 | structural + **property-tested** | authority = `scope∩MAX`; Hypothesis over arbitrary skill compositions ⇒ no widening; out-of-scope unreachable | — |

I3, I4, I7, I11 unchanged this pass (I4's empirical `-m podman` still pending — `runbook.md`).

## Techniques to apply (practical, in priority order)
1. **Make illegal states unrepresentable** (highest leverage): typed `MirrorView` (G3), citation-ID type (G1), `derived_from` with acyclic insert (G2). These *delete* whole test categories.
2. **Static import-graph lint** for I2 (e.g. an import-linter contract: `core` cannot import `edge`/sockets/HTTP).
3. **Exhaustive FSM checks** for the two tiny machines — the two-slot loader (I8) and the gate (I12) — their state spaces are small enough to enumerate.
4. **Property-based tests** (Hypothesis) for I6, I9, I10, I13 — the predicates over generated inputs.
5. **Runtime fail-closed guards** remain for I1, I8, I12; keep the I1 *assumption* (native bypass) documented and back it with OS isolation before any networked phase.

## Thesis
Each line of philosophy compiles to an invariant; each invariant has a tier and a discharge; the
highest-value move is to make the wrong thing *unrepresentable* rather than merely *tested*. The
single best outcome of writing this down was **exposing G1–G8** — which is exactly what
formalization is for: catching the underspecified before it ships.

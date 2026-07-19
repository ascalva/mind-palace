# Brainstorm — decision routing: owner attention as the scarcest resource; the threshold, compiled

> Captured by the orchestrator from a live owner brainstorm (2026-07-18 evening local, fable
> session-29). Owner's seed, verbatim (lightly elided): *"it's time to promote me … I have to hunt
> down multiple build files to mark ready, or design notes that get lost and one of us has to keep
> remembering to work on it … be strategic and secure about how claude can start handling some of
> the seal of approval … maybe you can group the permissions for a work track … there's some
> questions that are low stakes, low risk that the approval process can be better automated … I
> want to be more focused with the problems that matter, not the quick automation bug fix …
> a system redesign to make our workflow as efficient as possible."* Follow-up: *"not sure if we
> even need a label with any baggage, let's just design a system that will help me be more
> efficient, secure, automated."* Candidate to graduate into `dn-decision-routing`.

## 2026-07-19 UTC (session-29)

### The design brief, label-free

**The owner's attention is the system's scarcest budgeted resource; the workflow must spend it only
where it is irreplaceable — and prove it did.** Efficient = fewer interrupts, less re-orientation.
Secure = the automation cannot widen itself. Automated = code executes the owner's compiled
judgment.

### The apparent tension, and its resolution

The dyadic-epistemology capture (same evening, S9) holds that the human threshold is non-delegable
in an asymmetric dyad. This design does not delegate the threshold — **it compiles it**: the owner
ratifies a rubric once; deterministic code applies it per-instance; the agent classifies and
proposes but *never holds the approval pen*. "The model advises; code acts" extended to governance:
**the owner decides; policy acts.** Grounding (S8 of the same capture): delegation is the
interpretive leap licensed by accumulated E_proven — ~70 sealed plans, measured cost ratios, gates
held — and the audit ratchet keeps the grant proportional to that proven base.

### Three lanes (the diagnosis)

Today every decision is either an **interrupt** (owner, now, mid-flow) or **lost** (memory-based
queue). The redesign creates three lanes: **auto** (code approves within a ratified grant),
**batch** (accumulates on a docket; owner sweeps decision-ready items on their schedule),
**interrupt** (blockers + capability-changing only). Most of the win is interrupt/lost → batch;
automation is the second-order win.

### The five components (each an instance of an already-ratified pattern)

1. **The docket** — *a sensor over decision-state.* `scripts/docket.py` scans artifact front-matter
   and derives ONE view: everything awaiting the owner, sorted by stakes then AGE (staleness is what
   "gets lost" means). Never hand-maintained ⇒ cannot drift. Each row is **decision-ready**:
   one-paragraph context + orchestrator recommendation + stakes justification — deciding costs ~30
   seconds, not 10 minutes of re-orientation (the re-orientation tax is the silent killer).
2. **Stakes typing** — *the type system.* S0 mechanical (journals/docs — already agent-writable) ·
   S1 papercut (test-only, leaf surfaces, no new deps) · S2 conforming-to-charter · S3
   capability-changing. **The discriminator: changes what the system CAN DO → owner; changes what it
   happens to do within approved capability → automatable.**
3. **The policy** — *the law; the compiled threshold.* A ratified design note carrying a
   machine-readable grant block. A8's HEAD-keyed immutability already makes ratified notes
   agent-unwritable — REUSE (DRY): the agent can propose amendments, only the owner ratifies them.
   The grant structurally cannot widen itself.
4. **The checker** — *code acts.* Deterministic script: evaluates instance-vs-policy (write_scope ⊆
   granted surfaces; suite green; cost ≤ ceiling; cumulative envelope not exhausted), performs the
   flip, writes a **witnessed ledger entry** (the conditions that held — re-derivable, refutable:
   the witness law applied to approvals).
5. **The audit gauge** — *instrument + feedback.* Every auto-approval sampled at /triage; one
   pre-declared **demotion ratchet**: an approval later judged wrong demotes its whole class back to
   owner-gated. Trust extends on evidence, retracts on falsification, automatically.

Plus **track charters** — batch blessing as a workflow-axis scope grant: the owner ratifies a
program envelope once (write-scope union, cost budget, dependency shape — the formalization of
blessing bp-070+bp-069 in one sitting); conforming plans flip mechanically; deviation → interrupt.
**Blessing-as-grant is the scope algebra's pattern on the workflow axis**, and the pricing corollary
transfers verbatim: reversible + mechanically-checkable authority is cheap; irreversible or
interpretive authority is expensive.

### Security invariants

- Policy agent-immutable (A8); checker deterministic; gate-guard + Stop-gate audit continue
  unchanged.
- Every automated transition carries its witness; the ledger is append-only.
- Grants carry **cumulative blast envelopes** and expiry, not just per-instance checks (no boiling
  frog: individually-low-stakes approvals must not compose into a high-stakes state change).
- **Fail-closed:** any condition the checker cannot measure → route to owner. Never a guess (the
  partial-meet honesty, applied to approvals).
- The irreducible S3 set is NAMED IN THE POLICY: design ratification, kernel/boundary changes, new
  dependencies, `palace deploy`, and the policy itself. No automation path exists for these.
- **Bootstrap self-reference:** the automation cannot approve its own creation — the policy note
  enters through the fully-manual gate, by construction.

### The system measures itself

Decisions/week by lane · median age-at-decision · auto-approval audit pass rate · owner
interrupt count. If the docket is not shrinking interrupts, the gauge says so and the design is
revised rather than believed (structural-enforcement rule).

### Sequencing (by what needs ratification)

- **v1 — no governance change, papercut-tier (mintable as bp-072 with the cockpit strand):**
  `scripts/docket.py` + `palace bless` CLI (owner-run; one command instead of YAML hunting; gate
  semantics unchanged — the agent still never runs it). Solves "lost notes" + blessing friction
  before any governance change is even ratified.
- **v2 — needs ratification:** `stakes:` typing, the policy note, the S1 checker + ledger + audit
  loop + demotion ratchet.
- **v3 — after v2 proves out on the audit gauge:** track charters (S2 auto-bless); possibly
  auto-routing of finding dispositions.

```capsule
topic: decision-routing
date: 2026-07-18   # owner local; appended 2026-07-19 UTC

decisions:
  - No role labels; the design brief is: owner attention spent only where irreplaceable, provably.
  - The threshold is COMPILED, not delegated: owner ratifies policy; deterministic code applies it;
    the agent classifies/proposes and never holds the approval pen.
  - The stakes discriminator: capability-changing → owner forever; behavior-within-capability →
    automatable under a ratified grant.
  - The policy artifact is a ratified design note (reuses A8 agent-immutability; DRY).
  - v1 (docket + bless CLI) proceeds without any governance change; bp-069 remains the lead build —
    this work does not preempt the diamond.

parked:
  - decision: S2 charter automation (auto-bless of conforming plans)
    default: all blessings stay owner-by-hand
    re_entry: v2's audit gauge shows a clean sample run (size set in the policy note)
  - decision: typing workflow authority into the scope algebra (a new Authority coordinate)
    default: policy-document only; no type changes
    re_entry: a second consumer needs typed workflow authority
  - decision: auto-routing of finding dispositions
    default: findings route per the existing rules, owner decides
    re_entry: v2 proves out; papercut-class findings show a stable mechanical signature

open_questions:
  - The exact S1 condition set (candidate: write_scope ⊆ {tests/**, scripts/**, docs/** minus
    guarded}, no core/**, no new deps, suite green, cost ceiling, envelope arithmetic).
  - Ledger location and form (sqlite beside the run ledger vs an append-only file in docs/ops/).
  - Demotion granularity (whole class vs condition-subset) and audit sample size.
  - Does the checker live ops-side (launcher-adjacent) or as a bare script? (It acts on repo state,
    not the daemon — likely scripts/, but the deploy-gate precedent is ops-side.)

next_steps:
  - Mint bp-072 (v1: docket + bless CLI + cockpit; see owner-cockpit capture) — owner blesses
    manually, fittingly.
  - Fable design pass drafts dn-decision-routing (v2's policy + checker + gauge) for ratification;
    dn-inner-outer-core can ride the same pass.
  - Seals begin carrying read maps immediately (see owner-cockpit — no ratification needed).

references:
  - docs/brainstorms/dyadic-epistemology.md      # S8/S9 — the grounding and the sycophancy guard
  - docs/brainstorms/inner-outer-core.md          # the rhyme: same two-ring geometry
  - docs/brainstorms/owner-cockpit.md             # the presentation layer of the batch lane
  - CLAUDE.md                                     # the two owner-only gates; gate-guard; Stop-gate
  - docs/design-notes/capability-scope-algebra.md # blessing-as-grant's algebra; pricing corollary
  - docs/design-notes/agent-taxonomy.md           # §2.2 pricing law; the witness law
  - ops/lifecycle/launcher.py                     # deploy-gate precedent for policy-checked action
  - docs/findings/finding-0105.md                 # precedent: surgical gate mechanics, falsifier style
```

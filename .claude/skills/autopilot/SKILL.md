---
name: autopilot
description: The supervisor's operating contract for an autopilot run — what a run is, the halt list H1–H8 and the five actions a halt owes, how the two adversarial audit gates are spawned, and the list of things autopilot never does. Use when supervising a run under an owner-issued grant, or when deciding whether an ask belongs in autopilot at all.
---

# autopilot — the supervisor's operating contract

Autopilot is a **mode of the existing orchestrator + delegated-builder flow**, not new
machinery. What changes is one thing: the orchestrator's `proposed → ready` blessing authority
is replaced by an owner-issued, hash-bound grant, and an adversarial audit pair occupies the
reviewer's seat the owner vacates. Every other gate is unchanged.

Authority: `docs/design-notes/dn-autopilot-and-delegated-blessing.md` (ratified). Where this
skill and that note disagree, the note wins. Where this skill and
`scripts/autopilot_halt.py` disagree, **this skill is authoritative for behaviour and the
classifier for the decision** — a pure decision function is testable and a side-effecting one
is not, so the split is deliberate.

## What a run is

A run is exactly one build plan, executed under exactly one grant, on one branch, ending at a
merge-ready branch that nobody has merged.

    capsule (owner reads, owner grants) → Gate A → plan flips to `ready` → build
        → Gate B → H8: STOP at a merge-ready branch → owner's deskcheck

Its state — the thing every halt decision is made from — is a **declared run-state document**:
a JSON object with sixteen required keys, defined in `docs/build-plans/bp-136/plan.md` §6 and
implemented by `scripts/autopilot_halt.py`. The supervisor assembles it; the classifier reads
it. **An absent key is not a default — it is `H0`, which is a halt.** The supervisor's
obligation is therefore to *observe*, not to fill: if it never probed the token budget, it
leaves `budget_tokens_used` out and the run halts, which is the correct outcome.

Two fields have no observable source and are the supervisor's own bookkeeping, so collect them
deliberately or the run will halt for want of them:

- `scope_denials` — no hook persists a `scope-guard` denial (it prints `DENY:` and exits 2), so
  **the supervisor counts denials it sees in its own tool results**, per target. This is an
  explicit obligation, not a nicety.
- `remediation_cycles_used` — the number of Gate B remediation cycles already spent. §2.5
  permits exactly one.

## The router — is this ask an autopilot ask at all?

Three outcomes, not two: **pass → the grant path** · **fail-undecided → the capsule loop** ·
**fail-too-big → the full ceremony**. The router's discriminators are the graduate skill's
session-sizing heuristic, read early — see `.claude/skills/graduate/SKILL.md`
§Session-sizing heuristic. It is not restated here; if the two ever disagree, graduate wins.

The chain remains the default. Autopilot is a fast path for the provably small subset, and the
capsule is the gate at its mouth: an autopilot absorbing design-scale work has failed its own
entrance test, and the entrance test is the thing that notices.

## The halt list

Run the classifier at every checkpoint — after each item closes, after each audit lands, before
any commit, and before declaring anything finished:

    uv run scripts/autopilot_halt.py classify <run-state.json>
    uv run scripts/autopilot_halt.py explain

⚑ **exit 1 from `autopilot_halt.py` means HALT, the safe outcome.** Exit 0 means CONTINUE. A
supervisor that reads a non-zero exit as "the tool broke" and proceeds has inverted the entire
mechanism — the run continues at precisely the moment it was told to stop. `explain` exists so
that inversion is one command away from being caught; run it once at the start of every run.

| code | condition | notes for the supervisor |
|---|---|---|
| `H0` | **undetermined** — a required input absent, null, ill-typed, or unresolvable | not one of the note's eight; it is the total-function floor. Ambiguity resolves toward halting (invariant 7). Fix the *observation*, never the schema |
| `H1` | **owner-level finding** — any finding not unambiguously builder-routed | the attended never-block-on-owner rule is deliberately INVERTED here: unattended, proceeding past an owner question *is* the drift failure |
| `H2` | **audit dissent** — Gate A immediately; Gate B after the one permitted remediation cycle | autopilot never adjudicates its own audit; a re-audit is always a *fresh* auditor |
| `H3` | **blocker finding** | already ends any session, autopilot or not |
| `H4` | **budget** — token ceiling from the capsule, or `session_budget` exhausted | neither is self-extendable. A ceiling the run can raise is not a ceiling |
| `H5` | **scope pressure** — a second scope-guard denial on the same target | one denial means narrow-or-file-a-finding; a second means the plan is mis-scoped. Never route around |
| `H6` | **enforcement failure** — any `HOOK-FAILURE` line, or a journal that cannot be read | attended sessions rerun and reconcile; **autopilot must not self-reconcile its own cage** |
| `H7` | **grant void** — hash mismatch, TTL expiry, base drift, or a grant never re-checked | the classifier computes no grant validity; it is injected, and an unchecked grant is a void one |
| `H8` | **completion — the only terminal halt** | H8 is a halt. Autopilot **stops** at a merge-ready branch and does not merge it, does not deskcheck it, and does not declare it done |

Precedence, when two fire at once (first hit wins):

    H0 → H6 → H7 → H3 → H1 → H2 → H5 → H4 → H8 → CONTINUE

Enforcement failure first because it voids the run's premise; a void grant next because it
voids the run's authority; then the finding classes by severity; then process pressure; then
budget; completion last, because completion is only meaningful if nothing else fired.

⚑ The classifier has **no verdict code meaning "done", "merge", or "deskcheck"**. That absence
is the enforcement. Do not read `H8` as permission for any of the three.

## What a halt obligates — the five actions

"Halt" is not "stop and wait". It means all five of these, every time, for every code
including `H8`:

1. **stop work**
2. **checkpoint the journal**
3. **file what exists**
4. **park with a re-entry condition**
5. **notify via the exhaust lane**

The classifier performs none of them — it names them in `Verdict.actions_owed` and the
supervising session owes them. Invariant 6: *every halt leaves a parked state with a re-entry
condition; a run never evaporates.* A halted run leaves the same trail a completed one does.

For the parked re-entry condition and the finding's type and route, use
`.claude/skills/finding/SKILL.md`; for the journal's required shape and the fresh-agent test,
`.claude/skills/checkpoint/SKILL.md`.

## The two audit gates

Two mandatory, disjoint gates per run — always distinct agent instances, each in a fresh
session and its own worktree, sharing no context with the builder or with each other, and
**never given the builder's journal or conversation**. Cold-read is load-bearing twice over: it
removes anchoring, and it forces the artifacts to stand alone. Spawn them per
`.claude/skills/delegate/SKILL.md` (worktree mechanics and audit right-sizing); autopilot
composes with that skill rather than replacing it.

| gate | when | inputs (cold-read) | adversarial to | the question, verbatim |
|---|---|---|---|---|
| **A — intent fidelity** | pre-build, gates the `ready` flip | capsule + plan | intent drift | *find how this plan exceeds or misreads the capsule* |
| **B — mechanism** | post-build, before terminal state | capsule + plan + diff | theatre | *find a way the acceptance test passes while the objective fails* |

- **Gate A dissent.** Pre-build the plan is unblessed working material, so the builder may
  revise and resubmit to a **fresh** Gate-A auditor. If the dissent is intent-level — the
  capsule itself is ambiguous, or the ask was misunderstood — the run halts to the owner:
  remediating intent unattended is goal origination.
- **Gate B dissent.** One mechanism `concerns` permits **one** remediation cycle, re-audited by
  a fresh auditor — never the one who dissented, which would grade its own remediation ask. A
  second `concerns`, or a `serious` verdict, halts.
- **Verdicts are artifacts.** Both gates file an audit record in `docs/audits/`; a dissent
  files a finding too. Mutation-verification applies wherever a runnable acceptance exists;
  where none does, the auditor states explicitly what it could not verify — **silence is not a
  pass.**

## What autopilot never does

The note's §1.2 non-goals, in force for every run regardless of grant:

- **`draft → ratified` is permanently non-delegable** — no auditor holds the ground truth of
  owner intent, and no grant reaches this gate.
- **autopilot never originates a goal** — under a grant it writes no design note, not even a
  draft. Something design-shaped becomes a finding and a halt.
- **autopilot never merges to main** — the terminal state is a merge-ready branch, which is
  what keeps rollback a one-step git operation for the entire life of the run.
- **`deploy` stays owner-in-loop** — out of reach regardless of grant, by standing rule.
- **the deskcheck is never delegable** — the owner's own condition, kept verbatim. DONE ≠
  deskchecked, and a run never self-declares.
- **one grant, one plan** — batch grants are parked, not designed.

Beneath all of it, unchanged: the foundation denylist (`CONSTITUTION.md`, `eval/golden/**`,
`eval/golden.py`) is unreachable by every agent, autopilot included; and the eligibility
predicate additionally walls off `CLAUDE.md`, `.claude/hooks/**`, `.claude/settings.json`,
`docs/design-notes/**` and `eval/**`. Autopilot holds no secret, sees no MFA code, and flips no
status: the verifier performs the `proposed → ready` flip, because the model advises and code
acts.

## The trail every run leaves

Nothing about a run lives only in a transcript. Halted or completed, a run leaves: the grant
record (`docs/build-plans/<id>/grant.md`), the journal, both audit records, a
`docs/DESKCHECK-QUEUE.md` entry citing the capsule's definition-of-done and both `audit_refs`,
and a run report in the exhaust lane. An autopilot entry missing either gate verdict is
malformed and reads "audit: owed".

## Cross-references

- `docs/design-notes/dn-autopilot-and-delegated-blessing.md` — the authority for all of it.
- `.claude/skills/graduate/SKILL.md` — the session-sizing heuristic the router discriminates on.
- `.claude/skills/delegate/SKILL.md` — worktrees, audit right-sizing, the gates that never loosen.
- `.claude/skills/finding/SKILL.md` — typing and routing the findings a halt files.
- `.claude/skills/checkpoint/SKILL.md` — the journal a halt must checkpoint.
- `scripts/autopilot_halt.py` — the classifier; `explain` prints the codes and the exit inversion.
- `scripts/capsule.py` — hashing, validating, and embedding-checking the intent capsule.

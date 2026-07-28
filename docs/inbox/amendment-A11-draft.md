# Amendment A11 (DRAFT) — `role-state-and-scoped-handoff` §2.6 D4

> **Status: DRAFT, not landed.** Owner-directed 2026-07-27. Per that note's own §1.1, amendment
> text *"lands via a build plan after ratification, per the A1–A9 precedent"* — ratified notes are
> not agent-edited, and the hook layer being off tonight does not change that. This file is the
> paste-ready text. It is the **third** amendment `dn-typed-workflow-registry` §3(1) requires and
> does not list (discovered at graduation; it is what blocks `bp-150`).

## Owner instruction (verbatim, 2026-07-27)

> *"amend this note: role-state-and-scoped-handoff, it was written at a time when we didn't expect
> the hook migration would somehow make it all worse, needs to be amended, files are no longer the
> source of truth, and an agent's write scopes could be forced by role, scope still plays a part"*

## ⚑ The reading that shapes the amendment — D4 was mostly RIGHT

D4 rejected the scheduler queue as the handoff substrate on four grounds. On re-reading, **three
of the four are requirements the registry must satisfy, not objections it overturns.** An amendment
that simply says "ignore D4, the registry wins" would discard reasoning that is still correct and
would reintroduce the exact fragility D4 was written to prevent.

| D4's ground | still binding? | how the registry answers it |
|---|---|---|
| 1. **Fresh worktrees have no queue** — `data/**` is gitignored, absent from the checkout | ⚑ **YES — and it binds the registry too** | the registry lives at a machine-level path *outside* the repo, so a fresh clone or a worktree on another machine has **no registry either**. This is the live tension; §A11.2 resolves it. |
| 2. **Single-writer would be breached** | satisfied | the registry is single-writer by construction — that is the property that makes serial minting work |
| 3. **The artifact chain requires typed files** — no state in a blob git cannot diff, review, or ingest | ⚑ **YES** | answered by the **export**, which the queue never had: rendered markdown under an idempotence pin, with a CI ratchet asserting `export == working tree`. Reviewable, diffable, ingestable, readable in `nvim`. |
| 4. **The fresh-agent test reads files** | ⚑ **YES** | it still reads files — the exported ones. The test is unchanged. |

⇒ **D4's error was one word: it concluded "files are the source" from premises that only ever
established "files must remain READABLE and AUTHORITATIVE WHERE THE REGISTRY IS ABSENT."** That is
a weaker claim, and it is the one the amendment preserves.

---

## A11.1 — The substrate ruling is amended

**Replace** D4's ruling sentence (*"files as source; the queue as an input, never the source"*) with:

> **Ruling: the registry is the source of truth for state, identity, relations, transitions and
> ordering. Files are its EXPORT — authoritative prose, derived front-matter.** The scheduler queue
> remains what D4 made it: a read-only input to the DERIVED pane, never a substrate. That half of
> D4 is unchanged and was never in question.

## A11.2 — ⚑ The portability clause (this is the load-bearing addition)

> **In any checkout where the registry is not present — a fresh clone, a worktree on another
> machine, a CI runner — the EXPORT is authoritative and is treated as read-only.** Such a checkout
> may be read, built in, and reasoned from; it may not mint, transition, or seal. Those operations
> require the registry and fail closed with a named error, never a silent local fallback.

⚑ **Rationale, and why the fail-closed half matters more than the read half:** D4's ground 1 is not
dissolved by the registry, it is *inherited* by it. A checkout that cannot see the registry but
quietly writes front-matter would fork the truth — two divergent sources, no reconciliation, and the
divergence invisible until it corrupts. Refusing loudly is the only safe behaviour, and it is the
same discipline `dn-typed-workflow-registry` §2.9 already demands of the degraded mode.

`[INFERENCE]` The registry note's §2.8 placed the store outside the repo to make minting serial
across parallel worktrees *on one machine*. It did not address multi-machine or fresh-clone
checkouts. A11.2 is the smallest clause that closes that hole without re-opening the placement
decision.

## A11.3 — ⚑ Write scope becomes role-forced, with per-unit narrowing

> **An agent's writable surface is `role_ceiling ∩ unit_scope`, and it is imposed at DISPATCH, not
> checked at admission.** The registry spawns its workers (Claude SDK), so it constructs each
> worker's capability: the intersection *is* the tool/permission set the worker is given. The role
> fixes a ceiling no plan may widen; the unit's `write_scope` narrows within it. A plan naming a
> path outside its role's ceiling is a **malformed plan**, refused when the worker is constructed —
> the worker for it is never built.

⚑ **OWNER RULING 2026-07-27 — dispatch-time capability, not agent restraint:**

> *"you can edit a ratified note all you want, if you can't auth, it won't matter, it won't [be] an
> acceptable document, and the central system dispatches the workers with claude sdk, which means
> the system enforces that way, no need to force the hand of an agent, as we've seen, it cripples
> them"*

This supersedes the "refused at admission" reading drafted above it, and it is a **better**
mechanism than either option `dn-typed-workflow-registry` §2.6 weighed for `write_scope`
(land-time admission · worktree-as-scope). Both of those still *tell an agent no*. Dispatch-time
capability never has to: **the agent is not forbidden the path, it is never given it.** An
unauthorized write is not a denied act; it is an act with no warrant, and therefore not a document.

⇒ Two consequences worth stating plainly, because tonight demonstrated both:
1. **Self-restraint stops being load-bearing.** Tonight's builders held scope on discipline alone
   with no hook watching — which worked, and is exactly the assurance level that should never have
   been the mechanism. Under dispatch-time capability it isn't.
2. **The crippling was the cost, and it was real.** Forcing the agent's hand mid-work is what made
   the hook layer clog the machinery it protected. Constraining the *spawn* costs the worker
   nothing at runtime.

Concretely, from CLAUDE.md's existing role definitions (no new policy invented here):

| role | ceiling |
|---|---|
| **builder / scribe** | the plan's `write_scope` · its own `journal.md` · new files in `docs/findings/` |
| **orchestrator** | the artifact tree, `docs/PROGRESS.md`, `docs/inbox/**`, seat files |
| **every role** | ⚑ never the foundation denylist — `CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py` |

⚑ **Why this is stronger than per-unit scope alone, and why it belongs in THIS note:** it makes the
workflow layer obey non-negotiable **NN-6** — *"minted agents can't exceed their template's scope or
a pre-declared max."* Today that guarantee exists for minted agents and **not** for build plans: a
plan could name any path and the only thing standing between it and the write was a hook. Role-forced
scope makes the ceiling a property of *who is acting*, which is exactly this note's subject matter —
role state. It is also the clause that lets `dn-typed-workflow-registry`'s `bp-146` (write_scope as a
per-unit enforcement *level*) have something to be a level *of*.

`[INFERENCE]` That the ceiling should be refused at admission rather than intersected is a design
choice: a silently-narrowed plan looks like it succeeded while doing less than it declared, which is
the "check that passes without testing its claim" failure class (`finding-0249`).

## A11.4 — What is NOT amended

- **D4's queue ruling** — the queue stays a read-only DERIVED input. Unchanged.
- **D1/D2/D3/D5–D8** — untouched.
- **The fresh-agent drill (§2.11)** — unchanged, and now doubles as the falsifier for A11.2: it must
  still pass in a checkout with **no registry present**.
- **Clause (e′) / §2.10** — untouched by this amendment; it is retired separately under
  `dn-typed-workflow-registry` stage (iv), which is blocked on its own amendments.

## Falsifiers for A11

1. **A11.2 fails** if a registry-less checkout can mint, transition, or seal — or if it fails
   silently rather than with a named error.
2. **A11.3 fails** if any plan can name a path outside its role ceiling and still be admitted, or if
   the denylist is reachable from any role.
3. **A11.1 fails** if the export ever diverges from the registry without the CI ratchet reddening.
4. ⚑ **The whole amendment fails** if the fresh-agent drill (§2.11) stops passing in a checkout that
   has only the export.

## Landing

Per §1.1, via a build plan. `bp-150` is blocked on exactly this. Options, owner's choice:
**(a)** land A11 by hand now and unblock `bp-150` as graduated; **(b)** widen `bp-150`'s scope to
carry A11 as its first item. `[INFERENCE]` (a) is cleaner — an amendment carried by the plan it
unblocks is the note-amends-itself shape the A1–A9 precedent avoids.

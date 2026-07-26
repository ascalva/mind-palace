---
type: finding
id: finding-0222
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - .claude/hooks/_lib.py                      # clause (c) — the blessing/verdict audit
  - .claude/hooks/journal-gate.sh              # the Stop gate that runs it
  - docs/build-plans/bp-111/plan.md            # swept unverified by cffe515
  - docs/build-plans/bp-112/plan.md            # swept unverified by cffe515
  - docs/brainstorms/durable-chat-blessings.md  # why a blessing must be findable AS one
ftype: codebase
origin_plan: orchestrator
route: builder
resolution: null
---

# `git add -A` can absorb an owner blessing into an unrelated commit, and clause (c) is blind to it once committed

## What

Measured on myself this session, not hypothesised.

`cffe515` — a commit whose subject is `docs(bp-095): record the corrupted commit body of 7ab5187` —
also contains **two owner blessings**: `bp-111` and `bp-112`, each `status: proposed → ready`. They
were swept in by a `git add -A` while the owner was flipping plans by hand in parallel. The commit
message does not mention them. I did not verify their diffs before committing, which is the one thing
the blessing ceremony exists to require.

Minutes later the Stop gate's **clause (c) correctly blocked** on `bp-113` / `bp-114` — the same
transition, in the same session, by the same hand — because those two were still **uncommitted**.

That contrast is the finding:

```
bp-111, bp-112   flip absorbed into an unrelated commit   -> clause (c) SILENT  (already in HEAD)
bp-113, bp-114   flip sitting in the worktree             -> clause (c) BLOCKED (as designed)
```

Clause (c) compares the **worktree against HEAD**. It is therefore a *pre-commit* audit wearing a
*post-hoc* label. Once a blessing lands in a commit — by accident or otherwise — the gate has nothing
left to compare and reports clean.

Retroactive verification, done after the fact: both absorbed diffs *are* the status line alone, and
the owner authored both. **No substantive harm occurred.** The mechanism is the finding, not the
outcome.

## Why it matters

1. **A blessing's value is that it is findable AS a blessing.** `draft→ratified` and
   `proposed→ready` are the two gates the whole artifact chain rests on, and the ceremony's point is
   that each one becomes an accountable, greppable act — `bless(bp-NNN): proposed → ready`. Buried in
   a commit about a corrupted commit message, `bp-111`'s blessing is not discoverable by any audit
   that looks for blessings. The ledger says the flip happened; nothing says it was *blessed*.
2. **⚑ The same hole would hide an agent-authored flip.** Today the owner really did author these.
   But the identical `git add -A` in the identical situation would absorb a flip an *agent* made, and
   the post-hoc audit — the backstop that exists precisely because the pre-hoc guards are porous —
   would report clean. The only thing standing between a swept blessing and an unrecorded one is
   agent discipline, which is the thing this project explicitly refuses to rely on. `gate-guard`
   denies an agent *editing* the status pre-hoc, so the realistic path is exactly this one: a flip
   that arrives some other way and is then committed without scrutiny.
3. **It is the structural-enforcement doctrine failing on its own gate.** The standing rule is that a
   property is only real when a test or ratchet proves it. Clause (c) proves "no uncommitted blessing
   at session close". It does not prove "no unaccounted blessing this session", which is the property
   anyone reading the rule would assume it has.

## Re-entry condition

Nothing is parked; the session continued and `bp-113`/`bp-114` were committed properly as
`bless(bp-113, bp-114)` after verifying each diff.

Resolves when a blessing transition that lands *inside a commit* during a session is detected at the
Stop gate. The hook already records a **session baseline** sha for clause (e)
(`session-brief.sh` → `session-baseline`), so the material for the fix exists: audit blessing
transitions across `baseline..HEAD` **in addition to** worktree-vs-HEAD, and require that each such
transition appear in a commit whose subject declares it (`bless(...)`).

**Falsifier for any fix:** stage a `proposed → ready` flip together with an unrelated file, commit it
with an unrelated subject, and run the Stop gate. If it passes, the fix does not close this hole. A
fix that only re-checks the worktree has changed nothing.

## Routing

`codebase` → builder. The audit lives in `.claude/hooks/_lib.py` and the fix is bounded.

Two things deliberately **not** proposed as the fix:
- **"Stop using `git add -A`"** — a convention, and conventions are what this finding is about. It is
  worth doing anyway (and is now in the bp-095 journal as a lesson alongside the `-F -` heredoc rule),
  but it is not enforcement.
- **Blocking any commit that touches a plan's status line** — too blunt; `ready → in-progress` and
  `in-progress → complete` are legitimate non-blessing transitions that agents must be able to make.
  The audit has to discriminate the *blessing* transitions specifically, which is what clause (c)
  already knows how to do — it simply needs a wider window to look through.

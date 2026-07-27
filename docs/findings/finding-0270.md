---
type: finding
id: finding-0270
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - .claude/hooks/scope-guard.sh
  - docs/findings/finding-0269.md
ftype: codebase
origin_plan: bp-123
route: orchestrator
resolution: null
---

# scope-guard strips the leading `/` off an absolute path and judges it as repo-relative, so a builder cannot write to its own session scratchpad

## What

Attempting to write

```
/private/tmp/claude-501/-Users-ascalva-mind-palace/<session>/scratchpad/<file>.md
```

under active plan `bp-123` was denied with:

> `'private/tmp/claude-501/-Users-ascalva-mind-palace/<session>/scratchpad/<file>.md' is outside
> plan 'bp-123' write_scope [...]`

⚑ Note the reported path: **the leading `/` is gone.** The guard normalised an absolute path that is
*outside the repository entirely* into something that looks repo-relative, then tested that string
against `write_scope` and — inevitably — found no match.

## Why it matters

**A path outside `ROOT` is not in scope; it is not in the scope system's domain at all.** Conflating
"outside the repo" with "outside write_scope" makes the denial both wrong in principle and harmful in
practice:

- The harness assigns every session a scratchpad and instructs agents to use it for intermediate
  work in preference to `/tmp`. Under any active plan, that instruction **cannot be followed**.
- The workaround an agent will reach for is to write intermediate material *into the repo* — which is
  the outcome the scratchpad exists to prevent, and which puts untracked working files inside the
  very tree the guard protects. **The guard's failure mode pushes writes toward the protected
  surface, not away from it.**
- Encountered live during `bp-123`'s close, parking a drafted design note that then had to be held in
  context rather than on disk — precisely the context-economy loss the scratchpad is meant to avoid.

## Scope of the claim — what is NOT asserted

This finding does **not** claim the guard should permit arbitrary absolute paths. The correct posture
is almost certainly: a write whose realpath is **outside `ROOT`** is outside this guard's remit and
should be passed through to whatever else governs it — not silently re-interpreted as a repo path. If
there is a deliberate reason to deny out-of-tree writes from a builder (a defensible position), then
the *denial message* is still wrong, and the rule should be stated as its own clause rather than
emerging as an artefact of string-mangling.

⚑ Whether the correct behaviour is *pass through* or *deny explicitly* is a **design call**, not a
builder call — it decides whether a builder contract bounds the repo or bounds the agent. Routed
accordingly.

## Relation to finding-0269

Same family, different file: a check that answers its question by **manipulating a string** rather
than by consulting a typed model of the thing it is judging. `finding-0269` counts five private
grammars over journal text; this is a private grammar over paths. Both fail the same way — silently,
and in a direction that looks like correct enforcement.

## Status

Open. Routed to the orchestrator for the design call above. Not urgent for correctness of the tree
(nothing unsafe is permitted); urgent for agent ergonomics, since it silently defeats a standing
harness instruction on every plan-active session.
